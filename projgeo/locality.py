"""Locality analysis: is the inconsistency a smooth drift across the image?

Hypothesis tested (plan 3.5A, 7.4): a generator might be locally consistent
but drift gradually, so that lines of one family aim at slightly different
VPs depending on where they sit.  That would show up as spatially correlated
residuals.

* `residual_variogram` - correlation of signed angular residuals between
  segments of the same family, as a function of their distance.  A smooth
  drift makes near pairs agree more than far pairs.
* `consistent_twin` - the same segments re-aimed at the global VPs: one
  camera by construction, with the same layout and line counts.  Its
  statistics are the noise floor that any real excess is measured against
  (used by the regional analysis in `pipeline.py`).

Outcome: the variogram index is at chance for real and generated images in
every set, so the failure is disagreement between regions and structures,
not a smooth warp (report section 5.6).
"""

from __future__ import annotations

import numpy as np

from .geometry import unit
from .lines import Segments
from .vp import VPResult


def bin_curve(dist: np.ndarray, val: np.ndarray, edges: np.ndarray, stat=np.nanmedian) -> np.ndarray:
    """Per-bin statistic of `val` over `dist` bins (nan where empty)."""
    out = np.full(len(edges) - 1, np.nan)
    which = np.digitize(dist, edges) - 1
    for b in range(len(edges) - 1):
        m = which == b
        if m.sum() >= 5:
            out[b] = stat(val[m])
    return out


def consistent_twin(segs: Segments, vpr: VPResult, seed: int = 0,
                    noise_deg: float | None = None, cap_deg: float = 10.0) -> Segments:
    """Conditioning-matched null: re-aim every inlier segment exactly at its
    global VP (same midpoint and length) and add angular noise matched to the
    image's own inlier residual level.  The twin has the same line layout as
    the image but satisfies the single-camera hypothesis by construction, so
    any locality statistic computed on image minus twin is free of the
    conditioning confound.

    Membership uses the *uncensored* nearest-VP assignment within `cap_deg`
    (so lines that are inconsistent with the global camera are re-aimed too,
    otherwise a generated image's twin keeps exactly its inconsistent lines);
    the noise level comes from the tight inliers only.  Segments further than
    `cap_deg` from every VP are left untouched."""
    rng = np.random.default_rng(seed)
    xy = segs.xy.copy()
    mid = segs.midpoints
    L = segs.lengths
    use_nearest = vpr.nearest is not None and vpr.residuals_all is not None
    for k, v in enumerate(vpr.vps):
        if use_nearest:
            m = (vpr.nearest == k) & (vpr.residuals_all < cap_deg)
        else:
            m = vpr.labels == k
        if not m.any():
            continue
        if noise_deg is None:
            r = vpr.residuals[vpr.labels == k]
            sigma = float(np.sqrt(np.nanmean(r ** 2))) if np.isfinite(r).any() else 0.5
        else:
            sigma = noise_deg
        if abs(v[2]) > 1e-9 * np.linalg.norm(v[:2]):
            d = v[:2] / v[2] - mid[m]
        else:
            d = np.tile(v[:2], (m.sum(), 1))
        d = unit(d)
        d *= np.sign(np.sum(d * segs.directions[m], axis=1, keepdims=True) + 1e-12)
        ang = np.radians(rng.normal(0, sigma, m.sum()))
        c, s = np.cos(ang), np.sin(ang)
        d = np.stack([c * d[:, 0] - s * d[:, 1], s * d[:, 0] + c * d[:, 1]], axis=1)
        xy[m, :2] = mid[m] - 0.5 * L[m, None] * d
        xy[m, 2:] = mid[m] + 0.5 * L[m, None] * d
    return Segments(xy)


# ----------------------------------------------------------------------------
# Residual variogram: the cleanest locality statistic.
# ----------------------------------------------------------------------------

def signed_residuals(segs: Segments, vp: np.ndarray) -> np.ndarray:
    """Signed angle (deg) from the direction (midpoint -> VP) to the segment
    direction, in [-90, 90].  Sign is consistent across segments so spatially
    smooth camera drift shows up as spatially correlated residuals."""
    from .geometry import hom, line_direction
    M = hom(segs.midpoints)
    ideal = line_direction(np.cross(M, np.asarray(vp, float)[None, :]))
    D = segs.directions
    # flip segment direction to agree with ideal orientation, then signed angle
    s = np.sign(np.sum(D * ideal, axis=1) + 1e-12)
    D = D * s[:, None]
    cross = ideal[:, 0] * D[:, 1] - ideal[:, 1] * D[:, 0]
    dot = np.sum(ideal * D, axis=1)
    return np.degrees(np.arctan2(cross, dot))


def residual_variogram(segs: Segments, vpr: VPResult, width: int, height: int,
                       edges: np.ndarray, max_pairs_per_vp: int = 20000, seed: int = 0,
                       cap_deg: float = 10.0, exclude_collinear: bool = True) -> dict:
    """Semivariogram of signed residuals over same-VP inlier pairs.

    gamma(d) = 1/2 E[(r_i - r_j)^2 | dist = d], normalised by the residual
    variance so that independent residuals give gamma = 1 at every distance.
    rho(d) = 1 - gamma(d) is the spatial correlation: > 0 at short range and
    < 0 at long range means "locally consistent, globally inconsistent".
    Also returns the pooled correlation for near (< edges[2]) vs far pairs.

    Uses the *uncensored* nearest-VP assignment (every segment within
    `cap_deg` of its nearest VP) so that large, smooth drifts are not thrown
    out by the tight inlier threshold used for VP estimation.  Near-collinear
    pairs (fragments of one physical edge: perpendicular distance < 6 px and
    angle < 2 deg) are excluded because they share one residual by
    construction and would inflate short-range correlation."""
    rng = np.random.default_rng(seed)
    diag = float(np.hypot(width, height))
    M = segs.midpoints
    Ln = segs.lines
    D = segs.directions
    dist, sq = [], []
    use_nearest = vpr.nearest is not None and vpr.residuals_all is not None
    for k, v in enumerate(vpr.vps):
        if use_nearest:
            idx = np.flatnonzero((vpr.nearest == k) & (vpr.residuals_all < cap_deg))
        else:
            idx = np.flatnonzero(vpr.labels == k)
        if idx.size < 6:
            continue
        r = signed_residuals(segs[idx], v)
        r = r - r.mean()
        var = float(np.mean(r ** 2))
        if var < 1e-9:
            continue
        n_pairs = idx.size * (idx.size - 1) // 2
        if n_pairs <= max_pairs_per_vp:
            ii, jj = np.triu_indices(idx.size, k=1)
        else:
            ii = rng.integers(0, idx.size, max_pairs_per_vp)
            jj = rng.integers(0, idx.size, max_pairs_per_vp)
            keep = ii != jj; ii, jj = ii[keep], jj[keep]
        a, b = idx[ii], idx[jj]
        keep = np.ones(a.size, bool)
        if exclude_collinear:
            pd = np.abs(np.sum(Ln[a][:, :2] * M[b], axis=1) + Ln[a][:, 2])
            ang = np.degrees(np.arccos(np.clip(np.abs(np.sum(D[a] * D[b], axis=1)), 0, 1)))
            keep = ~((pd < 6) & (ang < 2))
        dist.append(np.linalg.norm(M[a][keep] - M[b][keep], axis=1) / diag)
        sq.append(0.5 * (r[ii][keep] - r[jj][keep]) ** 2 / var)
    if not dist:
        nb = len(edges) - 1
        return {"gamma": np.full(nb, np.nan), "rho": np.full(nb, np.nan), "n_pairs": 0,
                "rho_near": np.nan, "rho_far": np.nan}
    dist = np.concatenate(dist); sq = np.concatenate(sq)
    gamma = bin_curve(dist, sq, edges, stat=np.nanmean)
    near = dist < edges[2]; far = dist >= edges[len(edges) // 2]
    return {"gamma": gamma, "rho": 1 - gamma, "n_pairs": int(dist.size),
            "rho_near": float(1 - sq[near].mean()) if near.sum() >= 10 else np.nan,
            "rho_far": float(1 - sq[far].mean()) if far.sum() >= 10 else np.nan}
