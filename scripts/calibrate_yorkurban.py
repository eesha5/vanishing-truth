"""Phase 2: real-image calibration on YorkUrban.

For every image we run the L2/L3 suite three ways:
  * `lsd`  : our full pipeline (LSD detector + unconstrained VP estimator)
  * `gtl`  : our VP estimator on the hand-labelled inlier lines (estimator-only error)
  * `gtvp` : L3 computed directly on the ground-truth VPs (annotation + centre-pp floor)
and compare estimated VPs / focal length with the ground truth.

Outputs (outputs/yorkurban/): summary.csv, null_percentiles.json, ecdf.png,
vp_accuracy.png and a handful of overlays.
"""

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from tqdm import tqdm

from projgeo.camera import l3_report, vp_rays
from projgeo.datasets.yorkurban import YorkUrban
from projgeo.pipeline import analyze_segments, flatten_report
from projgeo.lines import detect_lsd
from projgeo.viz import plot_report


def vp_match_angles(est_vps, gt_vps, K):
    """Angle (deg) from each GT VP direction to the nearest estimated VP,
    both back-projected with the *true* K."""
    pp = np.array([K[0, 2], K[1, 2]])
    if len(est_vps) == 0:
        return np.full(len(gt_vps), np.nan)
    e = vp_rays(est_vps, K[0, 0], pp)
    g = vp_rays(gt_vps, K[0, 0], pp)
    return np.degrees(np.arccos(np.clip(np.abs(g @ e.T), 0, 1))).min(axis=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="data/real/YorkUrbanDB")
    ap.add_argument("--out", default="outputs/yorkurban")
    ap.add_argument("--thresh", type=float, default=2.0)
    ap.add_argument("--n-overlays", type=int, default=6)
    args = ap.parse_args()
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)

    ds = YorkUrban(args.root)
    rows = []
    for i, im in enumerate(tqdm(ds, total=len(ds))):
        w, h = im.width, im.height
        segs = detect_lsd(im.image)
        rep = analyze_segments(segs, w, h, thresh_deg=args.thresh)
        row = {"name": im.name, "n_gt_vps": int(len(np.unique(im.gt_labels))),
               "f_true": im.f}
        for k, v in flatten_report(rep).items():
            row[f"lsd_{k}"] = v
        ang = vp_match_angles(rep["_vp_result"].vps, im.vps, im.K)
        row["lsd_vp_err_max"] = float(np.nanmax(ang)); row["lsd_vp_err_mean"] = float(np.nanmean(ang))
        row["lsd_vp_recovered_2deg"] = int((ang < 2).sum()); row["lsd_vp_recovered_5deg"] = int((ang < 5).sum())

        rep_g = analyze_segments(im.gt_segments, w, h, thresh_deg=args.thresh)
        for k, v in flatten_report(rep_g).items():
            row[f"gtl_{k}"] = v
        ang = vp_match_angles(rep_g["_vp_result"].vps, im.vps, im.K)
        row["gtl_vp_err_max"] = float(np.nanmax(ang))

        l3g = l3_report(im.vps, w, h)
        for k in ("f_fit", "ortho_err_max_deg", "ortho_err_rms_deg", "f_spread",
                  "orthocenter_offset", "n_negative_f2"):
            row[f"gtvp_{k}"] = l3g.get(k)
        rows.append(row)
        if i < args.n_overlays:
            plot_report({**rep, "_image": im.image, "_segments": segs}, out / f"{im.name}_overlay.png")

    df = pd.DataFrame(rows)
    df.to_csv(out / "summary.csv", index=False)

    # ---- null percentiles of the residuals we will threshold on -----------
    keys = ["lsd_l2_capped_mean_deg", "lsd_l2_unexplained_frac", "lsd_ortho_err_max_deg",
            "lsd_orthocenter_offset", "lsd_f_spread", "gtl_ortho_err_max_deg",
            "gtvp_ortho_err_max_deg", "gtvp_orthocenter_offset"]
    qs = [0.5, 0.75, 0.9, 0.95, 0.99]
    null = {k: {f"p{int(q * 100)}": float(np.nanpercentile(df[k].astype(float), q * 100)) for q in qs}
            for k in keys if k in df}
    null["_n_images"] = int(len(df))
    (out / "null_percentiles.json").write_text(json.dumps(null, indent=1))

    # ---- report ------------------------------------------------------------
    f_ratio = df["lsd_f_fit"] / df["f_true"]
    f_ratio_g = df["gtl_f_fit"] / df["f_true"]
    print("\n=== YorkUrban calibration (n=%d) ===" % len(df))
    print("VP recovery (LSD pipeline): %.1f%% of GT VPs within 2 deg, %.1f%% within 5 deg" % (
        100 * df["lsd_vp_recovered_2deg"].sum() / df["n_gt_vps"].sum(),
        100 * df["lsd_vp_recovered_5deg"].sum() / df["n_gt_vps"].sum()))
    print("VP error (max per image), median: LSD %.2f deg | GT lines %.2f deg" % (
        df["lsd_vp_err_max"].median(), df["gtl_vp_err_max"].median()))
    print("Focal ratio f_fit/f_true, median [IQR]: LSD %.3f [%.3f, %.3f] | GT lines %.3f [%.3f, %.3f]" % (
        f_ratio.median(), f_ratio.quantile(.25), f_ratio.quantile(.75),
        f_ratio_g.median(), f_ratio_g.quantile(.25), f_ratio_g.quantile(.75)))
    print("Images with 3 VPs found (LSD): %d / %d" % ((df["lsd_n_vps"] == 3).sum(), len(df)))
    print("\nNull percentiles:")
    for k, v in null.items():
        if k.startswith("_"): continue
        print("  %-28s " % k + "  ".join(f"{p}={x:.3f}" for p, x in v.items()))

    # ---- figures -----------------------------------------------------------
    fig, axes = plt.subplots(2, 3, figsize=(13, 7))
    panels = [
        ("lsd_l2_capped_mean_deg", "L2 capped mean (deg)"),
        ("lsd_l2_unexplained_frac", "L2 unexplained fraction"),
        ("lsd_ortho_err_max_deg", "L3 ortho error max (deg)"),
        ("lsd_orthocenter_offset", "L3 orthocentre offset (/diag)"),
        ("lsd_f_spread", "L3 focal spread (CV)"),
    ]
    for ax, (k, lab) in zip(axes.ravel(), panels):
        x = np.sort(df[k].astype(float).dropna().values)
        ax.step(x, np.arange(1, len(x) + 1) / len(x), where="post", label="LSD pipeline")
        gk = k.replace("lsd_", "gtvp_")
        if gk in df:
            xg = np.sort(df[gk].astype(float).dropna().values)
            ax.step(xg, np.arange(1, len(xg) + 1) / len(xg), where="post", label="GT VPs", color="k", ls="--")
        ax.set_xlabel(lab); ax.set_ylabel("ECDF"); ax.grid(alpha=.3)
    axes[0, 2].legend(fontsize=8)
    ax = axes[1, 2]
    ax.hist(f_ratio.clip(0, 3), bins=30, alpha=.7, label="LSD"); ax.hist(f_ratio_g.clip(0, 3), bins=30, alpha=.5, label="GT lines")
    ax.axvline(1, color="k"); ax.set_xlabel("f_fit / f_true"); ax.legend(fontsize=8)
    fig.suptitle("YorkUrban real-image null distributions (n=%d)" % len(df))
    fig.tight_layout(); fig.savefig(out / "ecdf.png", dpi=110)

    fig, ax = plt.subplots(figsize=(6, 4))
    for col, lab in [("lsd_vp_err_max", "LSD pipeline"), ("gtl_vp_err_max", "GT lines")]:
        x = np.sort(df[col].dropna().clip(0, 30).values)
        ax.step(x, np.arange(1, len(x) + 1) / len(x), where="post", label=lab)
    ax.set_xlabel("max VP direction error per image (deg)"); ax.set_ylabel("ECDF"); ax.legend(); ax.grid(alpha=.3)
    fig.tight_layout(); fig.savefig(out / "vp_accuracy.png", dpi=110)


if __name__ == "__main__":
    main()
