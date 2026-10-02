"""Report figures for the Atlanta residual: one row per image set, median with
95 % interval, coloured and shaped by group (real / local model / frontier).

    python scripts/plot_dot_interval.py

Intervals come from projgeo.stats, the same functions atlanta_compare.py uses,
so the figures match the tables.
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from projgeo.stats import boot_median_ci, wilson_ci

# reference palette slots 1-3, validated all-pairs in light mode (dataviz skill)
GROUP_STYLE = {"real": ("#2a78d6", "o"), "local": ("#eb6834", "s"), "frontier": ("#1baf7a", "D")}
GROUP_LABEL = {"real": "real photographs", "local": "local open models", "frontier": "frontier closed models"}
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"


def summarise(df, rows):
    out = []
    for key, label, group in rows:
        d = df[df.set == key]
        lf = d[d.n_pairs >= 2].logf_spread.replace([np.inf, -np.inf], np.nan).dropna()
        m, lo, hi = boot_median_ci(lf)
        imp = d.any_impossible.dropna().astype(bool)
        plo, phi = wilson_ci(imp.sum(), len(imp))
        out.append(dict(label=f"{label}\n(n = {len(lf)})", group=group, m=m, lo=lo, hi=hi,
                        p=imp.mean() * 100, plo=plo * 100, phi=phi * 100))
    return out


def plot(rows, path, title, width=10.5, fs=1.0, row_h=0.62, pad_h=1.5):
    """fs scales every font and mark; the slide versions use a narrower figure and fs > 1."""
    n = len(rows)
    y = np.arange(n)[::-1]
    fig, axes = plt.subplots(1, 2, figsize=(width, row_h * n + pad_h), sharey=True,
                             gridspec_kw={"width_ratios": [1.25, 1]})
    real = [r for r in rows if r["group"] == "real"]
    for ax, (k, klo, khi, xlabel, fmt) in zip(axes, [
            ("m", "lo", "hi", "Atlanta log-focal spread (median, 95% CI)", "{:.2f}"),
            ("p", "plo", "phi", "Images with an impossible pair (%, 95% CI)", "{:.0f}%")]):
        lo_band, hi_band = min(r[klo] for r in real), max(r[khi] for r in real)
        ax.axvspan(lo_band, hi_band, color=GROUP_STYLE["real"][0], alpha=0.08, lw=0)
        for yi, r in zip(y, rows):
            c, mk = GROUP_STYLE[r["group"]]
            ax.plot([r[klo], r[khi]], [yi, yi], color=c, lw=2 * fs, solid_capstyle="round", zorder=2)
            ax.plot(r[k], yi, mk, color=c, ms=8 * fs, mec="white", mew=1.5, zorder=3)
            ax.text(r[k], yi + 0.2, fmt.format(r[k]), color=INK2, fontsize=8.5 * fs, ha="center", va="bottom")
        # slide versions are narrower with bigger type: break the label so the two panels' labels don't meet
        ax.set_xlabel(xlabel.replace(" (", "\n(") if fs > 1 else xlabel, color=INK, fontsize=9.5 * fs)
        ax.grid(axis="x", color=GRID, lw=0.8)
        ax.set_axisbelow(True)
        for s in ("top", "right", "left"):
            ax.spines[s].set_visible(False)
        ax.spines["bottom"].set_color(INK2)
        ax.tick_params(colors=INK2, labelsize=8.5 * fs, length=0)
        ax.set_ylim(-0.7, n - 0.3)
    axes[0].set_xlim(left=0)
    axes[1].set_xlim(0, 100)
    axes[0].set_yticks(y)
    axes[0].set_yticklabels([r["label"] for r in rows], color=INK, fontsize=9 * fs)
    present = list(dict.fromkeys(r["group"] for r in rows))
    handles = [plt.Line2D([], [], color=GROUP_STYLE[g][0], marker=GROUP_STYLE[g][1], ms=7 * fs, lw=2 * fs,
                          label=GROUP_LABEL[g]) for g in present]
    handles.append(plt.Rectangle((0, 0), 1, 1, color=GROUP_STYLE["real"][0], alpha=0.15,
                                 label="range of the real-photo intervals"))
    ncol = 2 if fs > 1 and len(handles) > 3 else len(handles)     # a long legend would widen a slide figure
    fig.legend(handles=handles, loc="upper center", ncol=ncol, frameon=False, fontsize=8.5 * fs,
               bbox_to_anchor=(0.55, 1.0))
    fig.suptitle(title, x=0.55, y=1.07, fontsize=11 * fs, color=INK)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("saved", path)


def main():
    rich = summarise(pd.read_csv("results/atlanta_scaling.csv"),
                     [("yorkurban", "York Urban", "real"), ("real-commons", "Commons", "real"),
                      ("sd15_rich", "SD 1.5", "local"), ("sdxl_rich", "SDXL", "local")])
    fr = summarise(pd.read_csv("results/frontier.csv"),
                   [("yorkurban", "York Urban", "real"), ("real-commons", "Commons", "real"),
                    ("sdxl_pilot", "SDXL", "local"), ("sd15_pilot", "SD 1.5", "local"),
                    ("gemini", "Gemini", "frontier"), ("gptimage", "ChatGPT", "frontier")])
    for rows, name, title in [(rich, "atlanta_dots", "Primary result: line-rich prompt set"),
                              (fr, "frontier_dots", "Frontier models: first prompt set")]:
        plot(rows, Path(f"results/{name}.png"), title)                       # report
        plot(rows, Path(f"results/{name}_slide.png"), title, width=8.0, fs=1.4,  # slides
             row_h=0.58, pad_h=1.5)


if __name__ == "__main__":
    main()
