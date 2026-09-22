"""Length scale of camera consistency: regional focal disagreement vs window size.

    python scripts/scale_curve.py --gen data/generated/sdxl_pilot --per-set 80

For each window size (fraction of the image side) we fit cameras in a 3x3
grid of overlapping windows and report the median pairwise |log f_i/f_j|,
for the image and for its consistent twin (same layout, one camera).  The
excess over the twin, as a function of window size, is the scale at which
the generator stops keeping a single camera.
"""

import argparse
from pathlib import Path

import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from tqdm import tqdm

from projgeo.datasets.yorkurban import YorkUrban
from projgeo.lines import detect_lsd
from projgeo.locality import consistent_twin
from projgeo.pipeline import analyze_segments
from projgeo.regional import regional_cameras

FRACS = [0.3, 0.4, 0.5, 0.65, 0.8]


def curve(img):
    h, w = img.shape[:2]
    segs = detect_lsd(img)
    rep = analyze_segments(segs, w, h, n_boot=0, regional=False)
    vpr, f = rep["_vp_result"], rep["L3"].get("f_fit")
    if f is None or len(vpr.vps) < 2:
        return None
    twin = consistent_twin(segs, vpr, seed=0)
    rows = []
    for fr in FRACS:
        a = regional_cameras(segs, vpr, f, w, h, n=3, frac=fr, min_segments=25)
        b = regional_cameras(twin, vpr, f, w, h, n=3, frac=fr, min_segments=25)
        rows.append({"frac": fr, "logf": a["logf_pairwise"], "logf_twin": b["logf_pairwise"],
                     "rot": a["rot_pairwise_deg"], "rot_twin": b["rot_pairwise_deg"],
                     "n_windows": a["n_windows"]})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gen", nargs="+", required=True)
    ap.add_argument("--per-set", type=int, default=80)
    ap.add_argument("--out", default="outputs/scale_curve")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    sets = {"real (YorkUrban)": [im.image for im in YorkUrban()][:args.per_set]}
    for g in args.gen:
        files = sorted(p for p in Path(g).iterdir() if p.suffix.lower() == ".png")[:args.per_set]
        sets[Path(g).name] = [cv2.resize(cv2.imread(str(p)), (640, 480), interpolation=cv2.INTER_AREA)
                              for p in files]
    recs = []
    for name, imgs in sets.items():
        for i, img in enumerate(tqdm(imgs, desc=name)):
            rows = curve(img)
            if rows:
                for r in rows:
                    recs.append({"set": name, "img": i, **r})
    df = pd.DataFrame(recs)
    df["logf_excess"] = df.logf - df.logf_twin
    df["rot_excess"] = df.rot - df.rot_twin
    df.to_csv(out / "scale_curve.csv", index=False)

    summary = df.groupby(["set", "frac"])[["logf", "logf_twin", "logf_excess", "rot", "rot_excess"]].median()
    print(summary.round(3).to_string())

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    for name, g in df.groupby("set"):
        m = g.groupby("frac")
        for ax, col, lab in [(axes[0], "logf", "median pairwise |log f_i/f_j|"),
                             (axes[1], "logf_excess", "excess over consistent twin"),
                             (axes[2], "rot_excess", "frame rotation excess (deg)")]:
            med = m[col].median()
            se = 1.2533 * m[col].std() / np.sqrt(m[col].count())
            ax.errorbar(med.index, med.values, yerr=se.values, marker="o", capsize=3, label=name)
            ax.set_xlabel("window size / image side")
            ax.set_ylabel(lab)
            ax.grid(alpha=.3)
    axes[1].axhline(0, color="k", lw=.8)
    axes[2].axhline(0, color="k", lw=.8)
    axes[0].legend()
    fig.suptitle("Camera consistency vs window size")
    fig.tight_layout()
    fig.savefig(out / "scale_curve.png", dpi=110)


if __name__ == "__main__":
    main()
