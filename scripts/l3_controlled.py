"""Content-controlled L3 experiment (plan 7.14, 7.17).

    python scripts/l3_controlled.py --real data/real/commons \
        --gen data/generated/sd15_pilot data/generated/sdxl_pilot data/generated/sdxl_3d \
        --out outputs/l3_controlled

The same applicability rule (`projgeo.selection.identifiability`, which never
looks at the residual) is applied to every set; L3 is then compared only among
images that pass.  The pass rate is itself reported, because "how often is a
single camera even identifiable?" is a result about the generator.

Real photographs additionally need `looks_uncropped` (a metadata criterion):
cropping moves the principal point, which centred-pp L3 assumes.  Generated
images are uncropped by construction, so the criterion is vacuous for them and
applying it to both sides keeps the comparison mirrored.
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

from projgeo.datasets.folder import image_files
from projgeo.camera import l3_report, select_manhattan_triple
from projgeo.datasets.yorkurban import YorkUrban
from projgeo.lines import detect_lsd
from projgeo.selection import identifiability, looks_uncropped
from projgeo.vp import estimate_vps

METRICS = [
    ("ortho_err_max_deg", "L3 orthogonality error, max pair (deg)"),
    ("ortho_err_rms_deg", "L3 orthogonality error, RMS (deg)"),
    ("f_spread", "focal spread across VP pairs"),
    ("orthocenter_offset", "orthocentre offset (/diagonal)"),
    ("hfov_deg", "fitted HFOV (deg)"),
    ("l3best_ortho_err_max_deg", "best-triple L3 (deg, 5 candidates)"),
]


def analyse(items, label, match_width=640, require_uncropped=False):
    rows = []
    for name, img, native_wh in tqdm(items, desc=label):
        if match_width and img.shape[1] != match_width:
            s = match_width / img.shape[1]
            img = cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
        h, w = img.shape[:2]
        segs = detect_lsd(img)
        vpr = estimate_vps(segs, w, h, n_vps=3)
        vpr5 = estimate_vps(segs, w, h, n_vps=5)
        idf = identifiability(segs, vpr, w, h)
        l3 = l3_report(vpr.vps, w, h)
        best = select_manhattan_triple(vpr5.vps, w, h, vpr5.support)
        uncropped = looks_uncropped(*native_wh) if native_wh else True
        rows.append({
            "path": name, "set": label,
            "identifiable": bool(idf["identifiable"]),
            "uncropped": bool(uncropped),
            "selected": bool(idf["identifiable"] and (uncropped or not require_uncropped)),
            "reject_reason": "; ".join(idf["reasons"])[:120],
            "n_segments": len(segs),
            "ortho_err_max_deg": l3.get("ortho_err_max_deg"),
            "ortho_err_rms_deg": l3.get("ortho_err_rms_deg"),
            "f_spread": l3.get("f_spread"),
            "orthocenter_offset": l3.get("orthocenter_offset"),
            "hfov_deg": l3.get("hfov_deg"),
            "l3best_ortho_err_max_deg": best.get("ortho_err_max_deg"),
        })
    return pd.DataFrame(rows)


def load_folder(folder, limit):
    files = image_files(folder, limit)
    meta_path = Path(folder) / "metadata.jsonl"
    native = {}
    if meta_path.exists():
        for line in meta_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            m = json.loads(line)
            if "orig_width" in m:
                native[m["file"]] = (m["orig_width"], m["orig_height"])
            elif "width" in m:
                native[m["file"]] = (m["width"], m["height"])
    out = []
    for p in files:
        img = cv2.imread(str(p))
        if img is None:
            continue
        out.append((p.name, img, native.get(p.name, (img.shape[1], img.shape[0]))))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--real", nargs="*", default=["data/real/commons"])
    ap.add_argument("--gen", nargs="+", required=True)
    ap.add_argument("--real-root", default="data/real/YorkUrbanDB")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--out", default="outputs/l3_controlled")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    ds = YorkUrban(args.real_root)
    sets = {"real (YorkUrban)": analyse([(im.name, im.image, (im.width, im.height))
                                         for im in ds][:args.limit or 999], "yorkurban", None)}
    for r in args.real:
        sets["real-" + Path(r).name] = analyse(load_folder(r, args.limit), "real-" + Path(r).name,
                                               require_uncropped=True)
    for g in args.gen:
        sets[Path(g).name] = analyse(load_folder(g, args.limit), Path(g).name)

    df = pd.concat(sets.values(), ignore_index=True)
    df.to_csv(out / "l3_controlled.csv", index=False)

    ref_name = "real (YorkUrban)"
    lines = ["### Applicability and L3 among selected images", "",
             "| quantity | " + " | ".join(sets) + " |", "|---|" + "---|" * len(sets)]
    lines.append("| images analysed | " + " | ".join(str(len(d)) for d in sets.values()) + " |")
    lines.append("| identifiable (3 usable VP families) | " +
                 " | ".join(f"{d.identifiable.mean():.0%}" for d in sets.values()) + " |")
    lines.append("| selected (identifiable + uncropped) | " +
                 " | ".join(f"{d.selected.mean():.0%} (n={int(d.selected.sum())})" for d in sets.values()) + " |")
    sel = {k: d[d.selected] for k, d in sets.items()}
    ref = sel[ref_name]
    for key, label in METRICS:
        cells, ps = [], []
        for name, d in sel.items():
            x = d[key].astype(float).dropna()
            cells.append(f"{x.median():.2f} [{x.quantile(.25):.2f}, {x.quantile(.75):.2f}]" if len(x) else "-")
            if name != ref_name and len(x) and len(ref[key].dropna()):
                ps.append(f"{name.split('_')[0]}: {mannwhitneyu(x, ref[key].astype(float).dropna()).pvalue:.2g}")
        lines.append(f"| {label} | " + " | ".join(cells) + " |")
        if ps:
            lines.append(f"| ... MWU p vs {ref_name} | " + ", ".join(ps) + " | " * max(len(sets) - 1, 1) + "|")
    p95 = np.nanpercentile(ref["ortho_err_max_deg"].astype(float), 95)
    lines.append(f"| share above real p95 ({p95:.2f} deg) | " +
                 " | ".join(f"{(d.ortho_err_max_deg.astype(float) > p95).mean():.0%}" for d in sel.values()) + " |")
    table = "\n".join(lines)
    (out / "l3_controlled_table.md").write_text(table)
    print("\n" + table)

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    for ax, (key, label) in zip(axes, [METRICS[0], METRICS[2], METRICS[4]]):
        for name, d in sel.items():
            x = np.sort(d[key].astype(float).dropna().values)
            if len(x):
                ax.step(x, np.arange(1, len(x) + 1) / len(x), where="post", label=f"{name} (n={len(x)})")
        ax.set_xlabel(label)
        ax.set_ylabel("ECDF")
        ax.grid(alpha=.3)
        if key == "ortho_err_max_deg":
            ax.set_xscale("log")
    axes[0].legend(fontsize=8)
    fig.suptitle("Content-controlled L3: only images where a single camera is identifiable")
    fig.tight_layout()
    fig.savefig(out / "l3_controlled.png", dpi=110)


if __name__ == "__main__":
    main()
