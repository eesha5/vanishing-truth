"""End-to-end analysis of one image (or a set of segments)."""

from __future__ import annotations

import cv2
import numpy as np

from .camera import atlanta_focal_consistency, l3_report, l3_uncertainty, select_manhattan_triple
from .lines import Segments, detect_lsd
from .locality import consistent_twin, residual_variogram
from .regional import regional_cameras
from .vp import VPResult, bootstrap_vps, estimate_vps

LOCALITY_EDGES = np.linspace(0.0, 1.0, 11)

# A VP counts as reliable when its inlier lines pin it down to better than
# this (bootstrap angular std in ray space) and it explains at least this
# fraction of total segment length.
RELIABLE_VP_STD_DEG = 1.0
RELIABLE_SUPPORT_FRAC = 0.05


def analyze_segments(segs: Segments, width: int, height: int, n_boot: int = 30,
                     regional: bool = True, n_candidates: int = 5, **vp_kwargs) -> dict:
    """Full constraint suite on one image's segments.

    L3 is reported three ways: on the three best-supported VPs (`L3`), on the
    candidate triple most consistent with one camera (`L3_best`, model
    selection over up to `n_candidates` VPs) and as Atlanta-world focal
    agreement between every horizontal VP and the vertical one (`L3_atlanta`).
    """
    vp_kwargs.setdefault("n_perm", 0)
    vpr_all: VPResult = estimate_vps(segs, width, height, n_vps=n_candidates, **vp_kwargs)
    vpr: VPResult = estimate_vps(segs, width, height, n_vps=3, **vp_kwargs)
    l2 = vpr.l2_summary()
    l3 = l3_report(vpr.vps, width, height)
    l3_best = select_manhattan_triple(vpr_all.vps, width, height, vpr_all.support)
    l3_best.pop("pairwise_focal", None)
    l3_atl = atlanta_focal_consistency(vpr_all.vps, vpr_all.support, width, height, min_support_frac=0.12)
    if n_boot and len(vpr.vps):
        samples = bootstrap_vps(segs, vpr, B=n_boot)
        l3["uncertainty"] = l3_uncertainty(vpr.vps, samples, width, height, l3.get("f_fit"))
        total = max(segs.lengths.sum(), 1e-9)
        frac = vpr.support / total
        rel = [bool((s < RELIABLE_VP_STD_DEG) and (fr >= RELIABLE_SUPPORT_FRAC))
               for s, fr in zip(l3["uncertainty"]["vp_std_deg"], frac)]
        l3["vp_support_frac"] = frac.tolist()
        l3["vp_reliable"] = rel
        l3["n_reliable_vps"] = int(sum(rel))
    vg = residual_variogram(segs, vpr, width, height, LOCALITY_EDGES)
    locality = {"rho": vg["rho"].tolist(), "rho_near": vg["rho_near"], "rho_far": vg["rho_far"],
                "index": (vg["rho_near"] - vg["rho_far"]) if np.isfinite(vg["rho_near"]) and np.isfinite(vg["rho_far"]) else None,
                "n_pairs": vg["n_pairs"]}
    reg = {}
    if regional and len(vpr.vps) >= 2 and l3.get("f_fit"):
        r = regional_cameras(segs, vpr, l3["f_fit"], width, height)
        reg = {k: r[k] for k in ("n_windows", "rot_pairwise_deg", "rot_adjacent_deg",
                                 "logf_pairwise", "radius_rot_deg", "radius_logf")}
        reg["_rot_vs_dist"] = r.get("rot_vs_dist")
        # Noise floor: the same segments re-aimed at the global VPs (one
        # camera by construction, same layout and line counts per window).
        twin = consistent_twin(segs, vpr, seed=0)
        rt = regional_cameras(twin, vpr, l3["f_fit"], width, height)
        for k in ("logf_pairwise", "radius_logf", "rot_pairwise_deg", "radius_rot_deg"):
            reg[f"{k}_twin"] = rt[k]
            reg[f"{k}_excess"] = (r[k] - rt[k]) if np.isfinite(r[k]) and np.isfinite(rt[k]) else np.nan
    return {
        "width": width, "height": height, "n_segments": len(segs),
        "vps": vpr.vps.tolist(),
        "L2": l2, "L3": l3, "L3_best": l3_best, "L3_atlanta": l3_atl,
        "locality": locality, "regional": reg, "n_candidates": int(len(vpr_all.vps)),
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
              "f_spread", "orthocenter_offset", "n_negative_f2", "n_reliable_vps"):
        row[k] = l3.get(k)
    loc = rep.get("locality", {})
    row["loc_index"] = loc.get("index"); row["loc_rho_near"] = loc.get("rho_near"); row["loc_rho_far"] = loc.get("rho_far")
    lb = rep.get("L3_best", {})
    row["l3best_model"] = lb.get("model")
    row["l3best_ortho_err_max_deg"] = lb.get("ortho_err_max_deg")
    row["l3best_hfov_deg"] = lb.get("hfov_deg")
    la = rep.get("L3_atlanta", {})
    row["atl_n_pairs"] = la.get("n_pairs")
    row["atl_frac_impossible"] = la.get("frac_impossible")
    row["atl_logf_spread"] = la.get("logf_spread")
    reg = rep.get("regional", {})
    for k in ("n_windows", "rot_pairwise_deg", "rot_adjacent_deg", "logf_pairwise",
              "radius_rot_deg", "radius_logf", "logf_pairwise_twin", "logf_pairwise_excess",
              "radius_logf_twin", "radius_logf_excess", "rot_pairwise_deg_excess", "radius_rot_deg_excess"):
        row[f"reg_{k}"] = reg.get(k)
    u = l3.get("uncertainty", {})
    for k in ("vp_std_max_deg", "ortho_err_max_boot_std", "ortho_err_max_boot_p95", "f_boot_cv"):
        row[k] = u.get(k)
    return row
