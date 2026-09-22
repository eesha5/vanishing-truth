"""Phase 3a pilot: real (YorkUrban) vs generated image sets, same pipeline.

    python scripts/pilot_compare.py --gen data/generated/sdxl_pilot --out outputs/pilot

Generated images are downscaled to YorkUrban's 640 px width by default so the
detector sees comparable resolution (--no-match-res to disable).
"""

import argparse
import json
from pathlib import Path

import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu
from tqdm import tqdm

from projgeo.datasets.yorkurban import YorkUrban
from projgeo.distortion import fit_radial_k1
from projgeo.lines import detect_lsd
from projgeo.locality import residual_variogram
from projgeo.pipeline import LOCALITY_EDGES, analyze_segments, flatten_report
from projgeo.vp import estimate_vps

REAL = "real (YorkUrban)"
METRICS = [
    ("l2_capped_mean_deg", "L2 capped mean (deg)", "higher = worse"),
    ("l2_unexplained_frac", "L2 unexplained fraction", "higher = worse"),
    ("l3best_ortho_err_max_deg", "L3 best-triple ortho error (deg)", "model selection over 5 VPs"),
    ("atl_frac_impossible", "Atlanta: impossible (h, v) pairs fraction", "higher = worse"),
    ("atl_logf_spread", "Atlanta: log-f spread across horizontals", "higher = worse"),
    ("ortho_err_max_deg", "L3 ortho error max (deg)", "higher = worse"),
    ("f_spread", "L3 focal spread", "higher = worse"),
    ("reg_radius_rot_deg", "Regional camera radius: rotation (deg)", "higher = no global camera"),
    ("reg_radius_logf", "Regional camera radius: |log f| ", "higher = no global camera"),
    ("reg_rot_adjacent_deg", "Adjacent-window frame rotation (deg)", "higher = worse gluing"),
    ("reg_logf_pairwise", "Pairwise |log f_i/f_j| (median)", "higher = worse"),
    ("reg_logf_pairwise_twin", "  ... same, consistent-twin noise floor", "estimator noise"),
    ("reg_logf_pairwise_excess", "  ... excess over twin", "higher = genuine inconsistency"),
    ("reg_radius_logf_excess", "Focal radius, excess over twin", "higher = genuine inconsistency"),
    ("reg_rot_pairwise_deg_excess", "Frame rotation, excess over twin (deg)", "higher = genuine inconsistency"),
    ("reg_n_windows", "# windows with a camera", "coverage"),
    ("loc_index", "Locality index (rho_near - rho_far)", "higher = more local"),
    ("loc_index_undist", "Locality index, distortion-corrected", "higher = more local"),
    ("k1", "Fitted radial distortion k1", "nuisance"),
    ("n_reliable_vps", "# reliable VPs", "lower = fewer coherent VPs"),
    ("n_segments", "# LSD segments", "content-match check"),
    ("hfov_deg", "Fitted HFOV (deg)", "camera configuration"),
]


def run_set(images, label, match_width=None):
    rows, rhos = [], []
    for name, img in tqdm(images, desc=label):
        if match_width and img.shape[1] != match_width:
            s = match_width / img.shape[1]
            img = cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
        h, w = img.shape[:2]
        segs = detect_lsd(img)
        rep = analyze_segments(segs, w, h)
        row = flatten_report(rep)
        row["path"] = name
        row["set"] = label
        if rep["L3"].get("f_fit") and len(rep["_vp_result"].vps):
            fit = fit_radial_k1(segs, rep["_vp_result"], rep["L3"]["f_fit"], w, h)
            vpr2 = estimate_vps(fit["segments"], w, h)
            vg = residual_variogram(fit["segments"], vpr2, w, h, LOCALITY_EDGES)
            row["k1"] = fit["k1"]
            row["loc_index_undist"] = vg["rho_near"] - vg["rho_far"]
        else:
            row["k1"] = np.nan
            row["loc_index_undist"] = np.nan
        rows.append(row)
        rhos.append(rep["locality"]["rho"])
    return pd.DataFrame(rows), np.array(rhos, dtype=float)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gen", nargs="+", required=True, help="generated image folders")
    ap.add_argument("--real-extra", nargs="*", default=[], help="additional real-photo folders")
    ap.add_argument("--hfov-band", nargs=2, type=float, default=[40, 60],
                    help="second table restricted to fitted HFOV in this band (deg)")
    ap.add_argument("--real-root", default="data/real/YorkUrbanDB")
    ap.add_argument("--out", default="outputs/pilot")
    ap.add_argument("--no-match-res", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    match_w = None if args.no_match_res else 640

    ds = YorkUrban(args.real_root)
    sets = {REAL: run_set([(im.name, im.image) for im in ds], "real", None)}
    for g in args.real_extra:
        files = sorted(p for p in Path(g).iterdir() if p.suffix.lower() in (".png", ".jpg", ".jpeg"))
        if args.limit:
            files = files[:args.limit]
        imgs = [(p.name, cv2.imread(str(p))) for p in files]
        sets["real-" + Path(g).name] = run_set(imgs, "real-" + Path(g).name, match_w)
    for g in args.gen:
        files = sorted(p for p in Path(g).iterdir() if p.suffix.lower() in (".png", ".jpg", ".jpeg"))
        if args.limit:
            files = files[:args.limit]
        imgs = [(p.name, cv2.imread(str(p))) for p in files]
        sets[Path(g).name] = run_set(imgs, Path(g).name, match_w)

    df = pd.concat([d for d, _ in sets.values()], ignore_index=True)
    df.to_csv(out / "summary.csv", index=False)
    real = sets[REAL][0]

    def build_table(frames, title):
        real_f = frames[REAL]
        lines = [f"### {title}", "",
                 "| metric | " + " | ".join(f"{k} (n={len(v)})" for k, v in frames.items()) + " | MWU p (vs real) |",
                 "|---|" + "---|" * (len(frames) + 1)]
        for key, label, note in METRICS:
            cells, ps = [], []
            for name, d in frames.items():
                x = d[key].astype(float).dropna()
                if len(x) == 0:
                    cells.append("-")
                    continue
                cells.append(f"{x.median():.3f} [{x.quantile(.25):.3f}, {x.quantile(.75):.3f}]")
                if name != REAL and len(real_f[key].dropna()) > 0:
                    p = mannwhitneyu(x, real_f[key].astype(float).dropna(), alternative="two-sided").pvalue
                    ps.append(f"{p:.2g}")
            lines.append(f"| {label} ({note}) | " + " | ".join(cells) + " | " + ", ".join(ps) + " |")
        for key in ("l2_capped_mean_deg", "ortho_err_max_deg", "reg_radius_rot_deg", "reg_radius_logf", "loc_index"):
            rn = np.sort(real_f[key].astype(float).dropna().values)
            if len(rn) == 0:
                continue
            cells = []
            for name, d in frames.items():
                x = d[key].astype(float).dropna().values
                pct = np.searchsorted(rn, x) / len(rn)
                cells.append(f"{100 * (pct > 0.95).mean():.0f}% above real p95")
            lines.append(f"| {key}: exceedance | " + " | ".join(cells) + " | |")
        return "\n".join(lines)

    frames = {k: d for k, (d, _) in sets.items()}
    table = build_table(frames, "All images")
    lo, hi = args.hfov_band
    band = {k: d[(d.hfov_deg >= lo) & (d.hfov_deg <= hi)] for k, d in frames.items()}
    table += "\n\n" + build_table(band, f"Fitted HFOV in [{lo:.0f}, {hi:.0f}] deg (matched camera configuration)")
    (out / "pilot_table.md").write_text(table)
    print("\n" + table)

    fig, axes = plt.subplots(3, 3, figsize=(15, 12))
    panels = [m for m in METRICS if m[0] in ("l2_capped_mean_deg", "l2_unexplained_frac", "ortho_err_max_deg",
                                              "f_spread", "reg_radius_rot_deg", "reg_radius_logf",
                                              "reg_rot_adjacent_deg", "loc_index")]
    for ax, (key, label, _) in zip(axes.ravel()[:8], panels):
        for name, (d, _) in sets.items():
            x = np.sort(d[key].astype(float).dropna().values)
            ax.step(x, np.arange(1, len(x) + 1) / len(x), where="post", label=name)
        ax.set_xlabel(label)
        ax.set_ylabel("ECDF")
        ax.grid(alpha=.3)
        if key in ("ortho_err_max_deg", "reg_radius_rot_deg"):
            ax.set_xscale("log")
    axes[0, 0].legend(fontsize=8)
    ax = axes[2, 2]
    centres = 0.5 * (LOCALITY_EDGES[1:] + LOCALITY_EDGES[:-1])
    for name, (_, rho) in sets.items():
        m = np.nanmean(rho, axis=0)
        se = np.nanstd(rho, axis=0) / np.sqrt(np.isfinite(rho).sum(axis=0).clip(1))
        ax.errorbar(centres, m, yerr=se, marker="o", ms=3, capsize=2, label=name)
    ax.axhline(0, color="k", lw=.8)
    ax.set_xlabel("segment separation / image diagonal")
    ax.set_ylabel("residual correlation rho(d)")
    ax.legend(fontsize=8)
    ax.grid(alpha=.3)
    fig.suptitle("Pilot: real vs generated under identical geometric tests")
    fig.tight_layout()
    fig.savefig(out / "pilot.png", dpi=110)
    json.dump({k: {"n": int(len(d))} for k, (d, _) in sets.items()}, (out / "sets.json").open("w"))


if __name__ == "__main__":
    main()
