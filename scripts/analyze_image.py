"""Run the L2/L3 constraint suite on one or more images.

    python scripts/analyze_image.py img1.jpg img2.png --out outputs/
"""

import argparse
import json
from pathlib import Path

import pandas as pd

from projgeo.pipeline import analyze_image, flatten_report
from projgeo.viz import plot_report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("images", nargs="+")
    ap.add_argument("--out", default="outputs")
    ap.add_argument("--thresh", type=float, default=2.0, help="inlier angle (deg)")
    ap.add_argument("--no-plot", action="store_true")
    args = ap.parse_args()

    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    rows = []
    for p in args.images:
        rep = analyze_image(p, thresh_deg=args.thresh)
        row = flatten_report(rep)
        rows.append(row)
        stem = Path(p).stem
        public = {k: v for k, v in rep.items() if not k.startswith("_")}
        (out / f"{stem}.json").write_text(json.dumps(public, indent=1))
        if not args.no_plot:
            plot_report(rep, out / f"{stem}_overlay.png")
        print(f"{stem}: segs={row['n_segments']} vps={row['n_vps']} "
              f"L2 capped={row['l2_capped_mean_deg']:.2f}° unexpl={row['l2_unexplained_frac']:.2f} "
              f"L3 ortho_max={row['ortho_err_max_deg']} f={row['f_fit']}")
    pd.DataFrame(rows).to_csv(out / "summary.csv", index=False)


if __name__ == "__main__":
    main()
