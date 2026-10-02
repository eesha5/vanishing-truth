"""The report figures that are drawn rather than computed from a results table.

    python scripts/make_report_figures.py

Writes to results/:
  architecture.png                 Figure 4.1, the pipeline flowchart
  explain_example.png              Figure 4.2, one real photo and one generated image, lines coloured
                                   by vanishing point with the focal length each direction implies
  commons_montage_credited.png     Figure 5.3, admitted Commons photos at low, moderate and very high
  commons_montage_credited.txt     Manhattan residual, and the photographers' credits for its caption
"""

import json
from pathlib import Path

import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch

from projgeo.datasets.yorkurban import YorkUrban
from projgeo.explain import disagreement_pct, draw, explain

RES = Path("results")


def architecture():
    fig, ax = plt.subplots(figsize=(11, 4.4))
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 4.4)
    ax.axis("off")

    def box(x, y, w, h, text, fc="#dbe7f5", ec="#2b4c7e", fs=8.6):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.04,rounding_size=0.12",
                                    fc=fc, ec=ec, lw=1.3))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs)

    def arrow(x1, y1, x2, y2, text=None):
        ax.annotate("", (x2, y2), (x1, y1), arrowprops=dict(arrowstyle="-|>", lw=1.3, color="#333"))
        if text:
            ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 0.12, text, ha="center", fontsize=7.6, color="#333")

    y1, hh = 2.85, 1.0
    box(0.1, y1, 1.45, hh, "Input image\n(real or generated)", fc="#eeeeee", ec="#555")
    box(1.9, y1, 1.45, hh, "Resize to\n640 px wide")
    box(3.7, y1, 1.65, hh, "LSD line\nsegment detection")
    box(5.7, y1, 2.0, hh, "Sequential RANSAC\nvanishing points\n(no Manhattan prior)")
    ax.add_patch(plt.Polygon([[8.95, y1 + hh + 0.15], [10.0, y1 + hh / 2], [8.95, y1 - 0.15],
                              [7.9, y1 + hh / 2]], fc="#fff2cc", ec="#b8860b", lw=1.3))
    ax.text(8.95, y1 + hh / 2, "Applicability\nrule: can this\nimage be\nmeasured?", ha="center", va="center",
            fontsize=7.8)
    for a, b in [(1.55, 1.9), (3.35, 3.7), (5.35, 5.7), (7.7, 7.9)]:
        arrow(a, y1 + hh / 2, b, y1 + hh / 2)
    box(10.1, y1 + 0.2, 0.85, 0.6, "No:\n'cannot\nmeasure'", fc="#f4cccc", ec="#a33", fs=7.4)
    arrow(10.0, y1 + hh / 2, 10.1, y1 + hh / 2)

    y2 = 0.45
    arrow(8.95, y1 - 0.15, 8.95, y2 + 1.25, "yes")
    box(7.25, y2, 3.4, 1.25, "Residuals per image\nL2  line concurrency (deg)\nAtlanta focal consistency (primary)\n"
                             "Manhattan orthogonality (secondary)\nL7 shadows (synthetic validation only)", fs=7.8)
    box(3.75, y2, 3.1, 1.25, "Compare with real-photo\ndistributions\n(bootstrap 95% CI,\nMann-Whitney test)", fs=8)
    box(0.1, y2, 3.25, 1.25, "Output\nper image: which rule failed, by how much\nper model: how far from real photos\n"
                             "+ residual-only classifier (AUC)", fc="#d9ead3", ec="#38761d", fs=7.8)
    arrow(7.25, y2 + 0.62, 6.85, y2 + 0.62)
    arrow(3.75, y2 + 0.62, 3.35, y2 + 0.62)
    fig.tight_layout()
    fig.savefig(RES / "architecture.png", dpi=140)
    plt.close(fig)


def explain_example():
    # published setting (no vertical-VP guard), as in the report's tables
    yu = {im.name: im.image for im in YorkUrban("data/real/YorkUrbanDB")}
    a = explain(yu["P1040814"], match_width=None, min_vert_dist_h=0)
    b = explain(cv2.imread("data/generated/gptimage/0023.png"), min_vert_dist_h=0)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
    draw(axes[0], a, "Real photograph (York Urban P1040814)\ndirections agree to within "
                     f"{disagreement_pct(a['atlanta']['logf_spread']):.0f}%  (calibrated f = 675 px)")
    draw(axes[1], b, "Generated image (ChatGPT, prompt 0023)\ndirections disagree by "
                     f"{disagreement_pct(b['atlanta']['logf_spread']):.0f}%")
    fig.tight_layout()
    fig.savefig(RES / "explain_example.png", dpi=130)
    plt.close(fig)


def commons_montage():
    f = pd.read_csv(RES / "frontier.csv").set_index("path")
    meta = {json.loads(line)["file"]: json.loads(line)
            for line in open("data/real/commons/metadata.jsonl", encoding="utf-8")}
    cols = [("Manhattan residual low", ["22786006.jpg", "144073395.jpg"]),
            ("Manhattan residual moderate", ["151607867.jpg", "121501894.jpg"]),
            ("Manhattan residual very high", ["84742407.jpg", "119858370.jpg"])]
    fig, axes = plt.subplots(2, 3, figsize=(11, 6.6))
    fig.subplots_adjust(left=0.01, right=0.99, top=0.88, bottom=0.01, wspace=0.05, hspace=0.18)
    letters = iter("abcdef")
    credits = []
    for c, (head, files) in enumerate(cols):
        fig.text((c + 0.5) / 3, 0.955, head, ha="center", fontsize=11, weight="bold")
        for r, fn in enumerate(files):
            ax = axes[r, c]
            img = cv2.cvtColor(cv2.imread(f"data/real/commons/{fn}"), cv2.COLOR_BGR2RGB)
            H = int(img.shape[1] * 0.70)                 # common 10:7 frame, centre crop or pad
            if img.shape[0] >= H:
                y0 = (img.shape[0] - H) // 2
                img = img[y0:y0 + H]
            else:
                pad = np.full((H, img.shape[1], 3), 255, np.uint8)
                y0 = (H - img.shape[0]) // 2
                pad[y0:y0 + img.shape[0]] = img
                img = pad
            ax.imshow(img)
            ax.set_xticks([])
            ax.set_yticks([])
            row, letter = f.loc[fn], next(letters)
            lf = row.logf_spread
            atl = f"{(np.exp(lf) - 1) * 100:.0f}%" if np.isfinite(lf) else "n/a"
            ax.set_title(f"({letter}) Manhattan {row.ortho_err_max_deg:.1f} deg  |  Atlanta {atl}", fontsize=9.5)
            credits.append(f"({letter}) {meta[fn]['author']}, {meta[fn]['license']}")
    fig.savefig(RES / "commons_montage_credited.png", dpi=120)
    plt.close(fig)
    # credits listed in letter order (a..f), matching the panel labels
    credits.sort(key=lambda s: s[1])
    (RES / "commons_montage_credited.txt").write_text("; ".join(credits), encoding="utf-8")


if __name__ == "__main__":
    architecture()
    explain_example()
    commons_montage()
    print("written: architecture.png, explain_example.png, commons_montage_credited.png/.txt")
