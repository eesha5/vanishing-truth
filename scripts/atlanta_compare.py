"""Primary analysis: Atlanta focal consistency (plan 7.20, 7.21, 7.23).

    python scripts/atlanta_compare.py --real data/real/commons \
        --gen data/generated/sdxl_rich data/generated/sd15_rich --out outputs/atlanta

For every image that passes the applicability rule, the vertical VP is found
by direction alone and each horizontal VP must imply the same focal length
with it.  Two statistics:

  * `logf_spread`  - spread of log f over the (horizontal, vertical) pairs;
    0 means every part of the scene agrees on how zoomed in the camera is.
  * `any_impossible` - whether some pair gives f^2 <= 0, i.e. no camera exists
    for that pair.  A proportion with a Wilson interval.

Valid in Manhattan *and* Atlanta worlds, so unlike the three-VP orthogonality
residual it does not penalise angled streets.  The per-image work is
`projgeo.explain.explain` with the published setting (no vertical-VP guard).
"""

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu
from tqdm import tqdm

from projgeo.datasets.folder import load_folder
from projgeo.datasets.yorkurban import YorkUrban
from projgeo.explain import explain
from projgeo.stats import boot_median_ci, wilson_ci


def run_set(items, label, match_width=640):
    rows = []
    for name, img in tqdm(items, desc=label):
        ex = explain(img, match_width=match_width, min_vert_dist_h=0)
        if not ex["admitted"]:
            continue
        atl = ex["atlanta"]
        rows.append({"path": name, "set": label,
                     "n_pairs": atl["n_pairs"],
                     "logf_spread": atl["logf_spread"],
                     "frac_impossible": atl["frac_impossible"],
                     "any_impossible": (atl["frac_impossible"] > 0) if np.isfinite(atl["frac_impossible"]) else np.nan,
                     "ortho_err_max_deg": ex["l3"].get("ortho_err_max_deg"),
                     "hfov_deg": ex["l3"].get("hfov_deg")})
    return pd.DataFrame(rows)


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
    for d in usable.values():
        m, lo, hi = boot_median_ci(d.logf_spread)
        cells.append(f"{m:.3f} [{lo:.3f}, {hi:.3f}]")
    lines.append("| **log-f spread**, median [95% CI] | " + " | ".join(cells) + " |")
    cells = []
    for d in sets.values():
        x = d.any_impossible.dropna().astype(bool)
        if len(x) == 0:
            cells.append("-")
            continue
        lo, hi = wilson_ci(x.sum(), len(x))
        cells.append(f"{x.mean():.0%} [{lo:.0%}, {hi:.0%}] (n={len(x)})")
    lines.append("| **images with an impossible (h,v) pair** | " + " | ".join(cells) + " |")
    cells = []
    for d in sets.values():
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
    imp = [sets[k].any_impossible.dropna().astype(bool) for k in names]
    vals = [x.mean() for x in imp]
    cis = [wilson_ci(x.sum(), max(len(x), 1)) for x in imp]
    errs = np.array([[v - lo, hi - v] for v, (lo, hi) in zip(vals, cis)]).T
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
