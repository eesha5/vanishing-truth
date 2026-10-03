"""The report figures that are drawn rather than computed from a results table.

    python scripts/make_report_figures.py

Writes to results/:
  architecture.png                 Figure 4.1, the pipeline flowchart
  app_workflow.png                 the demo app's workflow, upload to score
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


def app_workflow():
    fig, ax = plt.subplots(figsize=(13, 5.4))
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 5.4)
    ax.axis("off")

    def box(x, y, w, h, text, fc="#dbe7f5", ec="#2b4c7e", fs=9, weight="normal"):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.04,rounding_size=0.12",
                                    fc=fc, ec=ec, lw=1.3))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, weight=weight)

    def arrow(x1, y1, x2, y2, text=None, dy=0.13):
        ax.annotate("", (x2, y2), (x1, y1), arrowprops=dict(arrowstyle="-|>", lw=1.3, color="#333"))
        if text:
            ax.text((x1 + x2) / 2 + (0.18 if x1 == x2 else 0), (y1 + y2) / 2 + (0 if x1 == x2 else dy),
                    text, ha="center", va="center", fontsize=8.5, color="#333")

    # row 1: from the uploaded file to the applicability decision
    y1, h1 = 3.7, 1.2
    m1 = y1 + h1 / 2
    box(0.1, y1, 1.6, h1, "Upload image\n(PNG, JPG, WebP)\nor pick a\nbuilt-in example", fc="#eeeeee", ec="#555")
    box(2.05, y1, 1.5, h1, "Resize to\n640 px wide")
    box(3.9, y1, 1.75, h1, "Detect straight\nline segments\n(LSD)")
    box(6.0, y1, 2.05, h1, "Find vanishing points\n(sequential RANSAC,\nno right-angle\nassumption)")
    ax.add_patch(plt.Polygon([[9.45, y1 + h1 + 0.2], [10.75, m1], [9.45, y1 - 0.2], [8.15, m1]],
                             fc="#fff2cc", ec="#b8860b", lw=1.3))
    ax.text(9.45, m1, "Enough lines in\nthree directions\nto measure?", ha="center", va="center", fontsize=8.6)
    box(11.2, y1 + 0.15, 1.7, h1 - 0.3, "Cannot measure\n(no score: the app\nwill not guess)", fc="#f4cccc", ec="#a33",
        fs=8.6)
    for a, b in [(1.7, 2.05), (3.55, 3.9), (5.65, 6.0), (8.05, 8.15)]:
        arrow(a, m1, b, m1)
    arrow(10.75, m1, 11.2, m1, "no", dy=0.18)

    # row 2: measurements to score, right to left, then the output
    y2, h2 = 0.25, 2.55
    m2 = y2 + h2 / 2
    arrow(9.45, y1 - 0.2, 9.45, y2 + h2, "yes")
    box(7.95, y2, 3.0, h2, "10 geometry measurements\n\n"
                           "Focal disagreement between\ndirections (Atlanta, primary)\n"
                           "Impossible direction pairs (f² ≤ 0)\n"
                           "Right-angle error, Manhattan (2)\n"
                           "Lens-centre offset (orthocentre)\n"
                           "Line concurrency error (4)\n"
                           "Vanishing point uncertainty", fs=8.4)
    box(5.35, y2 + 0.45, 2.15, h2 - 0.9, "Random forest\n(300 trees)\n\nsees only the 10\nnumbers, never\nthe pixels",
        fs=8.6)
    box(2.9, y2 + 0.45, 2.0, h2 - 0.9, "Calibrate\n(Platt scaling)\n\nre-base to a\n50/50 prior", fs=8.6)
    arrow(7.95, m2, 7.5, m2)
    arrow(5.35, m2, 4.9, m2)
    arrow(2.9, m2, 2.45, m2)

    # output: the score bands the app shows, plus what explains them
    ax.text(1.27, y2 + h2 - 0.1, "Output", ha="center", va="top", fontsize=9.5, weight="bold")
    for k, (txt, fc, ec) in enumerate([("70% or more\nlooks generated", "#f4cccc", "#a33"),
                                       ("30% to 70%\nunclear", "#fff2cc", "#b8860b"),
                                       ("30% or less\nfits one real camera", "#d9ead3", "#38761d")]):
        box(0.15, y2 + 1.6 - k * 0.55, 2.25, 0.45, txt, fc=fc, ec=ec, fs=8)
    ax.text(1.27, y2 + 0.2, "+ lines coloured by direction\n+ \"why this score\" table",
            ha="center", va="center", fontsize=7.8, color="#333")
    fig.tight_layout()
    fig.savefig(RES / "app_workflow.png", dpi=150)
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
    app_workflow()
    explain_example()
    commons_montage()
    print("written: architecture.png, app_workflow.png, explain_example.png, commons_montage_credited.png/.txt")
