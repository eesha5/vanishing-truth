"""Does the primary result depend on mistaking a central depth VP for the
vertical VP?  (plan 7.25)

    python scripts/vertical_guard_sensitivity.py --out outputs/vguard

Re-runs the Atlanta residual on every admitted image with the vertical VP
required to lie at least k image-heights from the centre, for several k
(k = 0 is the published behaviour).  Also records how far the originally
chosen vertical VP was from the centre, which is the camera-tilt proxy used
for the level-camera check.
"""

import argparse
from pathlib import Path

import pandas as pd
from tqdm import tqdm

from projgeo.camera import atlanta_focal_consistency
from projgeo.datasets.folder import load_folder
from projgeo.datasets.yorkurban import YorkUrban
from projgeo.explain import explain

KS = [0.0, 0.5, 1.0, 2.0]


def run(items, label, match_width=640):
    rows = []
    for name, img in tqdm(items, desc=label):
        ex = explain(img, match_width=match_width, min_vert_dist_h=0)
        if not ex["admitted"]:
            continue
        v5, w, h = ex["vpr"], ex["width"], ex["height"]
        row = {"set": label, "path": name, "vert_dist_h": ex["vert_dist_h"]}
        for k in KS:
            a = ex["atlanta"] if k == 0 else atlanta_focal_consistency(
                v5.vps, v5.support, w, h, min_vert_dist=k * h)
            row[f"n_pairs_k{k}"] = a["n_pairs"]
            row[f"logf_k{k}"] = a["logf_spread"]
            row[f"imp_k{k}"] = a["frac_impossible"]
        rows.append(row)
    return pd.DataFrame(rows)


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
             run(load_folder("data/real/commons"), "real-commons")]
    for g in args.gen:
        parts.append(run(load_folder(g), Path(g).name))
    df = pd.concat(parts, ignore_index=True)
    df.to_csv(out / "vguard.csv", index=False)
    print("written", out / "vguard.csv", len(df))


if __name__ == "__main__":
    main()
