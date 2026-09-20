"""End-to-end analysis of one image (or a set of segments)."""

from __future__ import annotations

import cv2
import numpy as np

from .camera import l3_report
from .lines import Segments, detect_lsd
from .vp import VPResult, estimate_vps


def analyze_segments(segs: Segments, width: int, height: int, **vp_kwargs) -> dict:
    vpr: VPResult = estimate_vps(segs, width, height, **vp_kwargs)
    l2 = vpr.l2_summary()
    l3 = l3_report(vpr.vps, width, height)
    return {
        "width": width, "height": height, "n_segments": len(segs),
        "vps": vpr.vps.tolist(),
        "L2": l2, "L3": l3,
        "_vp_result": vpr,
    }


def analyze_image(path: str, **kwargs) -> dict:
    img = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(path)
    h, w = img.shape[:2]
    segs = detect_lsd(img)
    out = analyze_segments(segs, w, h, **kwargs)
    out["path"] = str(path)
    out["_segments"] = segs
    out["_image"] = img
    return out


def flatten_report(rep: dict) -> dict:
    """Scalar summary row for tables / CSV."""
    l2, l3 = rep["L2"], rep["L3"]
    row = {
        "path": rep.get("path"), "n_segments": rep["n_segments"], "n_vps": l3["n_vps"],
        "l2_rms_deg": l2["all"]["rms_deg"], "l2_mean_deg": l2["all"]["mean_deg"],
        "n_outliers": l2["all"]["n_outliers"],
        "l2_unexplained_frac": l2["all"].get("unexplained_frac"),
        "l2_capped_mean_deg": l2["all"].get("capped_mean_deg"),
    }
    for k in ("f_fit", "hfov_deg", "ortho_err_max_deg", "ortho_err_rms_deg",
              "f_spread", "orthocenter_offset", "n_negative_f2"):
        row[k] = l3.get(k)
    return row
