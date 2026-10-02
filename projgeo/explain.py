"""One-image explanation of the primary residual (plan 7.20), shared by the
report figure and the demonstration app.

`explain` follows `scripts/atlanta_compare.run_set` step for step: resample
to 640 px wide, LSD, three-VP estimate for the applicability rule, then a
five-VP estimate for Atlanta focal consistency.  With `min_vert_dist_h=0` it
reproduces the published population numbers exactly; the default of 1 image
height adds the vertical-VP guard of plan 7.25, which changes 0-5 % of images
and no conclusion.

It also returns `features`, the geometry-only residual vector the demo
app's classifier is trained on (`scripts/train_app_model.py`), so training
and serving share one code path.  Camera levelness (`vert_dist_h`) is
returned for the reliability warning but is deliberately *not* a feature:
generated images are level more often (plan 7.25), which is a style cue,
not a violation of projective geometry.
"""

import cv2
import numpy as np

from .camera import atlanta_focal_consistency, l3_report
from .lines import detect_lsd
from .selection import identifiability
from .vp import estimate_vps

ANALYSIS_WIDTH = 640
VERTICAL_COLOUR = "#ffd400"
HORIZONTAL_COLOURS = ["#e41a1c", "#377eb8", "#4daf4a", "#984ea3", "#ff7f00"]


FEATURES = ["l2_rms_deg", "l2_mean_deg", "l2_capped_mean_deg", "l2_unexplained_frac",
            "vp_std_max_deg", "ortho_err_max_deg", "ortho_err_rms_deg", "orthocenter_offset",
            "atl_logf_spread", "atl_frac_impossible"]
LEVEL_CAMERA_H = 50.0      # vertical VP farther than this (image heights): focal values unreliable


def explain(img_bgr: np.ndarray, match_width: int | None = ANALYSIS_WIDTH,
            min_vert_dist_h: float = 1.0) -> dict:
    img = img_bgr
    if match_width and img.shape[1] != match_width:
        s = match_width / img.shape[1]
        img = cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
    h, w = img.shape[:2]
    segs = detect_lsd(img)
    vpr = estimate_vps(segs, w, h, n_vps=3)
    ident = identifiability(segs, vpr, w, h)
    out = {"img": img, "width": w, "height": h, "segs": segs, "n_segments": len(segs),
           "admitted": bool(ident["identifiable"]), "reasons": list(ident["reasons"]),
           "vpr": vpr, "atlanta": None, "features": None, "vert_dist_h": float("nan")}
    if not out["admitted"]:
        return out
    vpr5 = estimate_vps(segs, w, h, n_vps=5)
    atl = atlanta_focal_consistency(vpr5.vps, vpr5.support, w, h, min_support_frac=0.08,
                                    min_vert_dist=min_vert_dist_h * h)
    l3 = l3_report(vpr.vps, w, h)
    l2 = vpr.l2_summary()["all"]
    out.update(vpr=vpr5, atlanta=atl, ortho_err_max_deg=l3.get("ortho_err_max_deg"),
               vert_dist_h=_vert_dist_h(vpr5.vps, atl["vertical"], w, h))
    out["features"] = {
        "l2_rms_deg": l2.get("rms_deg"), "l2_mean_deg": l2.get("mean_deg"),
        "l2_capped_mean_deg": l2.get("capped_mean_deg"),
        "l2_unexplained_frac": l2.get("unexplained_frac"),
        "vp_std_max_deg": float(np.max(ident["vp_std_deg"])) if ident.get("vp_std_deg") else np.nan,
        "ortho_err_max_deg": l3.get("ortho_err_max_deg"), "ortho_err_rms_deg": l3.get("ortho_err_rms_deg"),
        "orthocenter_offset": l3.get("orthocenter_offset"),
        "atl_logf_spread": atl["logf_spread"], "atl_frac_impossible": atl["frac_impossible"],
    }
    out["features"] = {k: (float(v) if v is not None else np.nan) for k, v in out["features"].items()}
    return out


def _vert_dist_h(vps, vert, w, h) -> float:
    """Distance of the chosen vertical VP from the image centre, in image heights."""
    if vert is None:
        return float("nan")
    v = vps[vert]
    if abs(v[2]) < 1e-12:
        return float("inf")
    return float(np.hypot(*(v[:2] / v[2] - [w / 2, h / 2])) / h)


def directions(ex: dict) -> list[dict]:
    """One entry per (horizontal, vertical) pair, with its colour and focal
    length in pixels (None when no camera can produce the pair)."""
    atl = ex["atlanta"]
    if not atl or atl["vertical"] is None:
        return []
    rows = []
    for k, pr in enumerate(atl["pairs"]):
        possible = pr["f2"] is not None and pr["f2"] > 0
        rows.append({"vp": pr["h"], "colour": HORIZONTAL_COLOURS[k % len(HORIZONTAL_COLOURS)],
                     "f_px": float(np.sqrt(pr["f2"])) if possible else None})
    return rows


def disagreement_pct(logf_spread: float) -> float:
    """Largest focal length over smallest, as a percentage excess."""
    return float((np.exp(logf_spread) - 1) * 100) if np.isfinite(logf_spread) else float("nan")


def draw(ax, ex: dict, title: str = "", legend: bool = True):
    """Image with segments coloured by VP family: yellow = vertical, one colour
    per horizontal direction, grey = everything else."""
    ax.imshow(cv2.cvtColor(ex["img"], cv2.COLOR_BGR2RGB))
    ax.set_xticks([]), ax.set_yticks([])
    if title:
        ax.set_title(title, fontsize=10)
    vpr, xy = ex["vpr"], ex["segs"].xy
    colour = {}
    if ex["atlanta"] and ex["atlanta"]["vertical"] is not None:
        colour[ex["atlanta"]["vertical"]] = VERTICAL_COLOUR
        for d in directions(ex):
            colour[d["vp"]] = d["colour"]
    for (x1, y1, x2, y2), lab in zip(xy, vpr.labels):
        c = colour.get(int(lab))
        if c is None:
            ax.plot([x1, x2], [y1, y2], color="#bbbbbb", lw=0.5, alpha=0.6)
        else:
            ax.plot([x1, x2], [y1, y2], color=c, lw=1.6)
    ax.set_xlim(0, ex["width"]), ax.set_ylim(ex["height"], 0)
    if legend and ex["atlanta"]:
        lines = ["vertical (reference)"]
        handles = [ax.plot([], [], color=VERTICAL_COLOUR, lw=3)[0]]
        for k, d in enumerate(directions(ex)):
            lab = f"direction {chr(65 + k)}: f = {d['f_px']:.0f} px" if d["f_px"] else \
                  f"direction {chr(65 + k)}: no camera possible"
            lines.append(lab)
            handles.append(ax.plot([], [], color=d["colour"], lw=3)[0])
        ax.legend(handles, lines, loc="lower left", fontsize=7.5, framealpha=0.85)
