"""L7 shadow consistency across image sets (automatic, no object segmentation).

    python scripts/l7_shadows.py --gen data/generated/sdxl_pilot data/generated/sd15_pilot \
        --real-extra data/real/commons --sunlit-only --out outputs/l7

Per image: shadow mask (threshold + morphology), major axis of each elongated
shadow component, concurrency of those axes at the sun-azimuth vanishing point,
and the distance of that vanishing point from the horizon implied by the
scene's horizontal VPs.  `--sunlit-only` keeps generated images whose prompt
mentions hard shadows (from metadata.jsonl).
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
from projgeo.datasets.yorkurban import YorkUrban
from projgeo.lines import detect_lsd
from projgeo.shadows import shadow_consistency
from projgeo.vp import estimate_vps

METRICS = [("shadow_frac", "shadow area fraction"),
           ("n_axes", "# elongated shadow axes"),
           ("axis_rms_deg", "shadow-axis concurrency RMS (deg)"),
           ("axis_max_deg", "shadow-axis concurrency max (deg)"),
           ("horizon_dist", "sun VP distance from horizon (/diag)")]


def run_set(items, label, match_width=640):
    rows = []
    for name, img in tqdm(items, desc=label):
        if match_width and img.shape[1] != match_width:
            s = match_width / img.shape[1]
            img = cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
        h, w = img.shape[:2]
        vpr = estimate_vps(detect_lsd(img), w, h, n_vps=3)
        r = shadow_consistency(img, vpr.vps)
        r.pop("shadow_vp", None)
        r.pop("horizon_vps", None)
        rows.append({"path": name, "set": label, **r})
    return pd.DataFrame(rows)


def load_folder(folder, sunlit_only, limit):
    folder = Path(folder)
    files = image_files(folder)
    meta_path = folder / "metadata.jsonl"
    if sunlit_only and meta_path.exists():
        meta = {json.loads(l)["file"]: json.loads(l) for l in meta_path.read_text(encoding="utf-8").splitlines() if l.strip()}
        keep = {f for f, m in meta.items()
                if "hard shadows" in m.get("prompt", "") or "sunlight" in m.get("prompt", "")}
        if keep:
            files = [p for p in files if p.name in keep]
    if limit:
        files = files[:limit]
    return [(p.name, cv2.imread(str(p))) for p in files]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gen", nargs="+", required=True)
    ap.add_argument("--real-extra", nargs="*", default=[])
    ap.add_argument("--real-root", default="data/real/YorkUrbanDB")
    ap.add_argument("--sunlit-only", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--out", default="outputs/l7")
    args = ap.parse_args()
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)

    sets = {"real (YorkUrban)": run_set([(im.name, im.image) for im in YorkUrban(args.real_root)][:args.limit or 999],
                                        "real", None)}
    for g in args.real_extra:
        sets["real-" + Path(g).name] = run_set(load_folder(g, False, args.limit), "real-" + Path(g).name)
    for g in args.gen:
        sets[Path(g).name] = run_set(load_folder(g, args.sunlit_only, args.limit), Path(g).name)

    df = pd.concat(sets.values(), ignore_index=True)
    df.to_csv(out / "l7_summary.csv", index=False)
    ref = sets["real (YorkUrban)"]

    lines = ["| metric | " + " | ".join(f"{k} (n={len(v)})" for k, v in sets.items()) + " | MWU p (vs real) |",
             "|---|" + "---|" * (len(sets) + 1)]
    for key, label in METRICS:
        cells, ps = [], []
        for name, d in sets.items():
            x = d[key].astype(float).dropna()
            cells.append(f"{x.median():.3f} [{x.quantile(.25):.3f}, {x.quantile(.75):.3f}]" if len(x) else "-")
            if name != "real (YorkUrban)" and len(x):
                ps.append(f"{mannwhitneyu(x, ref[key].astype(float).dropna()).pvalue:.2g}")
        lines.append(f"| {label} | " + " | ".join(cells) + " | " + ", ".join(ps) + " |")
    usable = ["| images with >= 3 shadow axes | " +
              " | ".join(f"{(d.status == 'ok').mean():.0%}" for d in sets.values()) + " | |"]
    table = "\n".join(lines + usable)
    (out / "l7_table.md").write_text(table)
    print("\n" + table)

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    for ax, (key, label) in zip(axes, [METRICS[2], METRICS[4], METRICS[1]]):
        for name, d in sets.items():
            x = np.sort(d[key].astype(float).dropna().values)
            if len(x):
                ax.step(x, np.arange(1, len(x) + 1) / len(x), where="post", label=name)
        ax.set_xlabel(label); ax.set_ylabel("ECDF"); ax.grid(alpha=.3)
        if key == "horizon_dist":
            ax.set_xscale("log")
    axes[0].legend(fontsize=8)
    fig.suptitle("L7: shadow consistency (automatic shadow-axis test)")
    fig.tight_layout(); fig.savefig(out / "l7.png", dpi=110)


if __name__ == "__main__":
    main()
