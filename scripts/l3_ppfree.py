"""Principal-point-free L3: a necessary condition valid for cropped / shifted
pinhole images.  With three finite VPs and unknown principal point, a camera
exists iff the VP triangle is acute (orthocentre inside the triangle gives
f^2 > 0).  We report, per set, among images with three reliable VPs:
  * fraction with an obtuse triangle  (no pinhole camera at all)
  * for acute triangles, the implied HFOV and how far the implied principal
    point lies from the image centre (crop / shift magnitude)

    python scripts/l3_ppfree.py --per-set 60
"""

import argparse
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
from tqdm import tqdm

from projgeo.camera import orthocenter
from projgeo.datasets.yorkurban import YorkUrban
from projgeo.geometry import to_inhomogeneous
from projgeo.lines import detect_lsd
from projgeo.pipeline import analyze_segments


def ppfree(vps, w, h):
    pts = [to_inhomogeneous(v) for v in vps]
    if len(pts) != 3 or any(p is None for p in pts):
        return None
    a, b, c = pts
    angs = []
    for p, q, r in ((a, b, c), (b, c, a), (c, a, b)):
        u, v = q - p, r - p
        angs.append(np.degrees(np.arccos(np.clip(u @ v / (np.linalg.norm(u) * np.linalg.norm(v) + 1e-12), -1, 1))))
    obtuse = max(angs) > 90
    oc = orthocenter(vps)
    out = {"obtuse": bool(obtuse), "max_angle": float(max(angs))}
    if not obtuse and oc is not None:
        f2 = -((a - oc) @ (b - oc))
        f = np.sqrt(f2) if f2 > 0 else np.nan
        out.update({"f_ppfree": float(f), "hfov_ppfree": float(2 * np.degrees(np.arctan(w / (2 * f)))) if f2 > 0 else np.nan,
                    "pp_offset": float(np.linalg.norm(oc - np.array([w / 2, h / 2])) / np.hypot(w, h))})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-set", type=int, default=60)
    args = ap.parse_args()
    sets = {"yorkurban": [im.image for im in YorkUrban()][:args.per_set]}
    for name, folder in [("commons", "data/real/commons"), ("sd15", "data/generated/sd15_pilot"), ("sdxl", "data/generated/sdxl_pilot")]:
        files = sorted(p for p in Path(folder).iterdir() if p.suffix.lower() in (".png", ".jpg"))[:args.per_set]
        sets[name] = [cv2.resize(cv2.imread(str(p)), (640, 480), interpolation=cv2.INTER_AREA) for p in files]
    rows = []
    for name, imgs in sets.items():
        for img in tqdm(imgs, desc=name):
            h, w = img.shape[:2]
            rep = analyze_segments(detect_lsd(img), w, h, regional=False)
            if rep["L3"].get("n_reliable_vps") != 3:
                continue
            r = ppfree(rep["_vp_result"].vps, w, h)
            if r:
                rows.append({"set": name, **r, "ortho_centred": rep["L3"]["ortho_err_max_deg"]})
    df = pd.DataFrame(rows)
    df.to_csv("outputs/l3_ppfree.csv", index=False)
    for name, g in df.groupby("set", sort=False):
        acute = g[~g.obtuse]
        print(f"{name:10s} n(3 reliable VPs)={len(g):3d}  obtuse (no camera): {g.obtuse.mean():.0%}  "
              f"| acute: HFOV median {acute.hfov_ppfree.median():.0f} deg, pp offset median {acute.pp_offset.median():.3f}, "
              f"pp offset > 0.25: {(acute.pp_offset > 0.25).mean():.0%}")


if __name__ == "__main__":
    main()
