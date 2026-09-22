"""Does the L3 focal fit recover the EXIF focal length on real photos from
many cameras?  (Phase 2b validation; YorkUrban was a single camera.)

    python scripts/validate_focal_commons.py

Uses f_px_est = width * f35 / 36 from the 35 mm-equivalent EXIF focal.
Caveats: EXIF f35 is rounded, images may be cropped (moves the principal
point), and the comparison is only meaningful on images with three reliable
VPs.  We report the log-ratio distribution and its correlation.
"""

import json
from pathlib import Path

import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import spearmanr
from tqdm import tqdm

from projgeo.lines import detect_lsd
from projgeo.pipeline import analyze_segments

root = Path("data/real/commons")
recs = [json.loads(l) for l in (root / "metadata.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
recs = [r for r in recs if r.get("f_px_est")]
rows = []
for r in tqdm(recs):
    img = cv2.imread(str(root / r["file"]))
    if img is None:
        continue
    h, w = img.shape[:2]
    rep = analyze_segments(detect_lsd(img), w, h, regional=False)
    l3 = rep["L3"]
    if l3.get("status") != "ok":
        continue
    rows.append({"file": r["file"], "f_exif": r["f_px_est"] * w / r["thumb_width"], "f_fit": l3["f_fit"],
                 "n_rel": l3.get("n_reliable_vps", 0), "ortho": l3["ortho_err_max_deg"],
                 "hfov_exif": 2 * np.degrees(np.arctan(w / (2 * r["f_px_est"] * w / r["thumb_width"])))})
import pandas as pd
df = pd.DataFrame(rows)
df["log_ratio"] = np.log(df.f_fit / df.f_exif)
df.to_csv("outputs/commons_focal_validation.csv", index=False)
for label, g in [("all", df), ("3 reliable VPs", df[df.n_rel == 3])]:
    rho = spearmanr(g.f_fit, g.f_exif).correlation
    print(f"{label:16s} n={len(g):3d}  median log(f_fit/f_exif)={g.log_ratio.median():+.3f}  "
          f"IQR [{g.log_ratio.quantile(.25):+.3f}, {g.log_ratio.quantile(.75):+.3f}]  "
          f"within 20%: {(g.log_ratio.abs() < np.log(1.2)).mean():.0%}  spearman={rho:.2f}")
g = df[df.n_rel == 3]
fig, ax = plt.subplots(figsize=(5, 5))
ax.loglog(g.f_exif, g.f_fit, ".", alpha=.6)
lim = [300, 5000]
ax.plot(lim, lim, "k-", lw=.8)
ax.plot(lim, [1.2 * x for x in lim], "k--", lw=.5)
ax.plot(lim, [x / 1.2 for x in lim], "k--", lw=.5)
ax.set_xlabel("EXIF focal length (px)")
ax.set_ylabel("L3 fitted focal length (px)")
ax.set_title(f"Commons real photos, 3 reliable VPs (n={len(g)})")
ax.grid(alpha=.3, which="both")
fig.tight_layout()
fig.savefig("outputs/commons_focal_validation.png", dpi=110)
