"""Does the primary result depend on mistaking a central depth VP for the
vertical VP?  (plan 7.25)

    python scripts/vertical_guard_sensitivity.py --out outputs/vguard

Re-runs the Atlanta residual on every admitted image with the vertical VP
required to lie at least k image-heights from the centre, for several k
(k = 0 is the published behaviour).  Records, per image, how far the
originally chosen vertical VP was from the centre, so the share of
suspect choices can be counted per set.
"""

import argparse
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
from tqdm import tqdm

from projgeo.camera import atlanta_focal_consistency
from projgeo.datasets.yorkurban import YorkUrban
from projgeo.lines import detect_lsd
from projgeo.selection import identifiability
from projgeo.vp import estimate_vps

KS = [0.0, 0.5, 1.0, 2.0]


def vert_dist_h(vps, vert, w, h):
    if vert is None:
        return np.nan
    v = vps[vert]
    if abs(v[2]) < 1e-12:
        return np.inf
    return float(np.hypot(*(v[:2] / v[2] - [w / 2, h / 2])) / h)


def run(items, label, match_width=640):
    rows = []
    for name, img in tqdm(items, desc=label):
        if match_width and img.shape[1] != match_width:
            s = match_width / img.shape[1]
            img = cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
        h, w = img.shape[:2]
        segs = detect_lsd(img)
        if not identifiability(segs, estimate_vps(segs, w, h, n_vps=3), w, h)["identifiable"]:
            continue
        v5 = estimate_vps(segs, w, h, n_vps=5)
        row = {"set": label, "path": name}
        for k in KS:
            a = atlanta_focal_consistency(v5.vps, v5.support, w, h, min_support_frac=0.08,
                                          min_vert_dist=k * h)
            if k == 0:
                row["vert_dist_h"] = vert_dist_h(v5.vps, a["vertical"], w, h)
            row[f"n_pairs_k{k}"] = a["n_pairs"]
            row[f"logf_k{k}"] = a["logf_spread"]
            row[f"imp_k{k}"] = a["frac_impossible"]
        rows.append(row)
    return pd.DataFrame(rows)


def folder(d):
    fs = sorted(p for p in Path(d).iterdir() if p.suffix.lower() in (".png", ".jpg", ".jpeg"))
    return [(p.name, cv2.imread(str(p))) for p in fs]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gen", nargs="+", default=["data/generated/sdxl_rich", "data/generated/sd15_rich",
                                                  "data/generated/sdxl_pilot", "data/generated/sd15_pilot",
                                                  "data/generated/gemini", "data/generated/gptimage"])
    ap.add_argument("--out", default="outputs/vguard")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    parts = [run([(im.name, im.image) for im in YorkUrban("data/real/YorkUrbanDB")], "yorkurban", None),
             run(folder("data/real/commons"), "real-commons")]
    for g in args.gen:
        parts.append(run(folder(g), Path(g).name))
    df = pd.concat(parts, ignore_index=True)
    df.to_csv(out / "vguard.csv", index=False)
    print("written", out / "vguard.csv", len(df))


if __name__ == "__main__":
    main()
