"""Per-image radial lens distortion as a nuisance parameter.

Real photographs carry barrel / pincushion distortion that bends straight
edges and therefore produces spatially correlated VP residuals (plan 7.8).
We fit a single-coefficient radial model per image by minimising the capped
residuals of all segments to their (re-refined) VPs, and expose the
undistorted segments so any residual statistic can be recomputed on them.

Model (normalised coordinates about the image centre, scaled by f):
    p_undistorted = p * (1 + k1 * |p|^2)
"""

from __future__ import annotations

import numpy as np

from .lines import Segments
from .vp import VPResult, angular_residuals, refine_vp
from .geometry import normalizing_transform, unit


def undistort_segments(segs: Segments, k1: float, f: float, width: int, height: int) -> Segments:
    pp = np.array([width / 2.0, height / 2.0])
    p = (segs.xy.reshape(-1, 2) - pp) / f
    r2 = np.sum(p ** 2, axis=1, keepdims=True)
    return Segments(((p * (1 + k1 * r2)) * f + pp).reshape(-1, 4))


def _cost(segs: Segments, vpr: VPResult, width: int, height: int, cap_deg: float) -> float:
    """Length-weighted capped residual after re-refining each VP on the
    (uncensored) nearest-assigned segments."""
    T = normalizing_transform(width, height)
    S = segs.transformed(T)
    tot, wsum = 0.0, 0.0
    for k, v in enumerate(vpr.vps):
        idx = np.flatnonzero((vpr.nearest == k) & (vpr.residuals_all < cap_deg))
        if idx.size < 4:
            continue
        vk = refine_vp(S[idx], unit(T @ v), S.lengths[idx])
        r = np.minimum(angular_residuals(S[idx], vk), cap_deg)
        w = S.lengths[idx]
        tot += float(np.sum(w * r ** 2))
        wsum += float(w.sum())
    return tot / max(wsum, 1e-9)


def fit_radial_k1(segs: Segments, vpr: VPResult, f: float, width: int, height: int,
                  grid=(-0.15, 0.15, 13), cap_deg: float = 10.0) -> dict:
    """Coarse-to-fine 1-D search for k1.  Returns k1, the cost curve and the
    undistorted segments."""
    lo, hi, n = grid
    ks = np.linspace(lo, hi, n)
    costs = np.array([_cost(undistort_segments(segs, k, f, width, height), vpr, width, height, cap_deg)
                      for k in ks])
    j = int(costs.argmin())
    # one refinement step around the best coarse value
    step = (hi - lo) / (n - 1)
    ks2 = np.linspace(ks[j] - step, ks[j] + step, 9)
    costs2 = np.array([_cost(undistort_segments(segs, k, f, width, height), vpr, width, height, cap_deg)
                       for k in ks2])
    j2 = int(costs2.argmin())
    k1 = float(ks2[j2])
    return {"k1": k1, "cost_undistorted": float(costs2[j2]),
            "cost_raw": float(costs[np.argmin(np.abs(ks))]),
            "segments": undistort_segments(segs, k1, f, width, height)}
