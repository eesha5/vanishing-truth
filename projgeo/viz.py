"""Overlay plots: segments coloured by VP cluster, VPs, horizon."""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .geometry import to_inhomogeneous
from .lines import Segments
from .vp import VPResult

COLORS = ["#e41a1c", "#377eb8", "#4daf4a", "#984ea3", "#ff7f00"]


def plot_report(rep: dict, out_path: str, image: np.ndarray | None = None,
                segs: Segments | None = None, margin: float = 0.6) -> None:
    vpr: VPResult = rep["_vp_result"]
    segs = segs if segs is not None else rep.get("_segments")
    image = image if image is not None else rep.get("_image")
    w, h = rep["width"], rep["height"]
    l3 = rep["L3"]

    fig, ax = plt.subplots(figsize=(11, 8))
    if image is not None:
        ax.imshow(image[..., ::-1] if image.ndim == 3 else image, cmap="gray",
                  extent=(0, w, h, 0))
    else:
        ax.set_facecolor("white")
    for lab, col in [(-1, "#bbbbbb")] + [(k, COLORS[k % len(COLORS)]) for k in range(len(vpr.vps))]:
        m = vpr.labels == lab
        if not m.any():
            continue
        for x1, y1, x2, y2 in segs.xy[m]:
            ax.plot([x1, x2], [y1, y2], color=col, lw=1.2 if lab >= 0 else 0.6)
    # extended canvas so nearby VPs are visible
    xlim = [-margin * w, (1 + margin) * w]
    ylim = [(1 + margin) * h, -margin * h]
    for k, v in enumerate(vpr.vps):
        p = to_inhomogeneous(v)
        if p is not None and xlim[0] < p[0] < xlim[1] and ylim[1] < p[1] < ylim[0]:
            ax.plot(p[0], p[1], "o", ms=9, mec="k", color=COLORS[k % len(COLORS)])
            ax.annotate(f"VP{k}", p, xytext=(6, 6), textcoords="offset points")
    if l3.get("orthocenter") is not None:
        oc = l3["orthocenter"]
        ax.plot(oc[0], oc[1], "x", ms=10, mew=2, color="k")
        ax.plot(w / 2, h / 2, "+", ms=10, mew=2, color="k")
    ax.add_patch(plt.Rectangle((0, 0), w, h, fill=False, ec="k", lw=1))
    ax.set_xlim(xlim); ax.set_ylim(ylim); ax.set_aspect("equal")
    l2 = rep["L2"]["all"]
    title = (f"L2 capped mean {l2.get('capped_mean_deg', float('nan')):.2f}°, "
             f"unexplained {100 * l2.get('unexplained_frac', float('nan')):.0f}%  |  ")
    if l3.get("status") == "ok":
        title += (f"L3 ortho err max {l3['ortho_err_max_deg']:.2f}°, f={l3['f_fit']:.0f}px "
                  f"(HFOV {l3['hfov_deg']:.0f}°), neg f²: {l3['n_negative_f2']}")
        if l3.get("orthocenter_offset") is not None:
            title += f", orthocentre offset {l3['orthocenter_offset']:.3f}"
    ax.set_title(title, fontsize=9)
    fig.tight_layout()
    fig.savefig(out_path, dpi=110)
    plt.close(fig)
