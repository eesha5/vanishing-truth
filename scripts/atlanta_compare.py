"""Primary L3 analysis: Atlanta focal consistency (plan 7.20).

    python scripts/atlanta_compare.py --real data/real/commons \
        --gen data/generated/sdxl_rich data/generated/sd15_rich --out outputs/atlanta

For every image that passes the residual-independent applicability rule, the
vertical VP is identified by direction alone and each horizontal VP must imply
the same focal length with it.  Two statistics:

  * `logf_spread`  - spread of log f over the (horizontal, vertical) pairs;
    0 means every part of the scene agrees on how zoomed in the camera is.
  * `any_impossible` - whether some pair gives f^2 <= 0, i.e. no camera exists
    for that pair at all.  Reported as a proportion with a Wilson interval,
    because it is a categorical claim.

Valid in Manhattan *and* Atlanta worlds, so unlike the three-VP orthogonality
residual it does not penalise angled streets and multi-frame scenes.
"""

import argparse
from pathlib import Path

import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu
from statsmodels.stats.proportion import proportion_confint
from tqdm import tqdm

from projgeo.camera import atlanta_focal_consistency, l3_report
from projgeo.datasets.yorkurban import YorkUrban
from projgeo.lines import detect_lsd
from projgeo.selection import identifiability
from projgeo.vp import estimate_vps


def boot_median_ci(x, n_boot=2000, seed=0):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    if len(x) < 3:
        return (np.nan, np.nan, np.nan)
    rng = np.random.default_rng(seed)
    meds = [np.median(rng.choice(x, len(x), replace=True)) for _ in range(n_boot)]
    return float(np.median(x)), float(np.percentile(meds, 2.5)), float(np.percentile(meds, 97.5))


def run_set(items, label, match_width=640):
    rows = []
    for name, img in tqdm(items, desc=label):
        if match_width and img.shape[1] != match_width:
            s = match_width / img.shape[1]
            img = cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
        h, w = img.shape[:2]
        segs = detect_lsd(img)
        vpr = estimate_vps(segs, w, h, n_vps=3)
        if not identifiability(segs, vpr, w, h)["identifiable"]:
            continue
        vpr5 = estimate_vps(segs, w, h, n_vps=5)
        atl = atlanta_focal_consistency(vpr5.vps, vpr5.support, w, h, min_support_frac=0.08)
        l3 = l3_report(vpr.vps, w, h)
        rows.append({"path": name, "set": label,
                     "n_pairs": atl["n_pairs"],
                     "logf_spread": atl["logf_spread"],
                     "frac_impossible": atl["frac_impossible"],
                     "any_impossible": (atl["frac_impossible"] > 0) if np.isfinite(atl["frac_impossible"]) else np.nan,
                     "ortho_err_max_deg": l3.get("ortho_err_max_deg"),
                     "hfov_deg": l3.get("hfov_deg")})
    return pd.DataFrame(rows)


def load_folder(folder, limit):
    files = sorted(p for p in Path(folder).iterdir() if p.suffix.lower() in (".png", ".jpg", ".jpeg"))
    if limit:
        files = files[:limit]
    return [(p.name, cv2.imread(str(p))) for p in files]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--real", nargs="*", default=["data/real/commons"])
    ap.add_argument("--gen", nargs="+", required=True)
    ap.add_argument("--real-root", default="data/real/YorkUrbanDB")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--out", default="outputs/atlanta")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    sets = {"real (YorkUrban)": run_set([(im.name, im.image) for im in YorkUrban(args.real_root)],
                                        "yorkurban", None)}
    for r in args.real:
        sets["real-" + Path(r).name] = run_set(load_folder(r, args.limit), "real-" + Path(r).name)
    for g in args.gen:
        sets[Path(g).name] = run_set(load_folder(g, args.limit), Path(g).name)

    df = pd.concat(sets.values(), ignore_index=True)
    df.to_csv(out / "atlanta.csv", index=False)

    lines = ["### Atlanta focal consistency (selected images only)", "",
             "| quantity | " + " | ".join(sets) + " |", "|---|" + "---|" * len(sets)]
    lines.append("| selected images | " + " | ".join(str(len(d)) for d in sets.values()) + " |")
    usable = {k: d[d.n_pairs >= 2] for k, d in sets.items()}
    lines.append("| with >= 2 horizontal families | " +
                 " | ".join(str(len(d)) for d in usable.values()) + " |")
    cells = []
    for k, d in usable.items():
        m, lo, hi = boot_median_ci(d.logf_spread)
        cells.append(f"{m:.3f} [{lo:.3f}, {hi:.3f}]")
    lines.append("| **log-f spread**, median [95% CI] | " + " | ".join(cells) + " |")
    cells = []
    for k, d in sets.items():
        x = d.any_impossible.dropna().astype(bool)
        if len(x) == 0:
            cells.append("-")
            continue
        lo, hi = proportion_confint(int(x.sum()), len(x), method="wilson")
        cells.append(f"{x.mean():.0%} [{lo:.0%}, {hi:.0%}] (n={len(x)})")
    lines.append("| **images with an impossible (h,v) pair** | " + " | ".join(cells) + " |")
    cells = []
    for k, d in sets.items():
        m, lo, hi = boot_median_ci(d.ortho_err_max_deg)
        cells.append(f"{m:.2f} [{lo:.2f}, {hi:.2f}]")
    lines.append("| Manhattan orthogonality (secondary) | " + " | ".join(cells) + " |")

    lines += ["", "**Mann-Whitney p for log-f spread:**", ""]
    for ref in [k for k in sets if k.startswith("real")]:
        ps = []
        for k in sets:
            if k == ref or k.startswith("real"):
                continue
            x = usable[k].logf_spread.dropna()
            y = usable[ref].logf_spread.dropna()
            if len(x) >= 3 and len(y) >= 3:
                ps.append(f"{k}: p = {mannwhitneyu(x, y).pvalue:.3g}")
        if ps:
            lines.append(f"* vs {ref}: " + "; ".join(ps))
    table = "\n".join(lines)
    (out / "atlanta_table.md").write_text(table, encoding="utf-8")
    print("\n" + table)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    for name, d in usable.items():
        x = np.sort(d.logf_spread.dropna().values)
        if len(x):
            axes[0].step(x, np.arange(1, len(x) + 1) / len(x), where="post", label=f"{name} (n={len(x)})")
    axes[0].set_xlabel("Atlanta log-f spread")
    axes[0].set_ylabel("ECDF")
    axes[0].legend(fontsize=8)
    axes[0].grid(alpha=.3)
    names = list(sets)
    vals = [sets[k].any_impossible.dropna().astype(bool).mean() for k in names]
    errs = np.array([[v - proportion_confint(int(sets[k].any_impossible.dropna().sum()),
                                             max(len(sets[k].any_impossible.dropna()), 1), method="wilson")[0],
                      proportion_confint(int(sets[k].any_impossible.dropna().sum()),
                                         max(len(sets[k].any_impossible.dropna()), 1), method="wilson")[1] - v]
                     for k, v in zip(names, vals)]).T
    axes[1].bar(range(len(names)), vals, yerr=np.abs(errs), capsize=4,
                color=["#377eb8" if n.startswith("real") else "#e41a1c" for n in names])
    axes[1].set_xticks(range(len(names)))
    axes[1].set_xticklabels([n.replace("real (YorkUrban)", "YorkUrban") for n in names], rotation=20, fontsize=8)
    axes[1].set_ylabel("share with an impossible (h,v) VP pair")
    axes[1].grid(alpha=.3, axis="y")
    fig.suptitle("Atlanta focal consistency: does every part of the image imply one camera?")
    fig.tight_layout()
    fig.savefig(out / "atlanta.png", dpi=110)


if __name__ == "__main__":
    main()
