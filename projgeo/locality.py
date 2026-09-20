"""Locality analysis: does geometric consistency degrade with image distance?

Central hypothesis of the project (plan §3.5A, §7.4): generators are
*locally* consistent (nearby lines agree on a VP) but lack a *global* camera
(distant lines disagree).  Two estimators of "consistency vs separation":

1. `pairwise_locality` — for two inlier segments of the same VP, their
   intersection is a local two-line VP estimate; we measure its ray-space
   angle to the global VP as a function of the distance between the segments.
   Known confound: nearby, nearly-parallel segments give ill-conditioned
   intersections, so *estimator* noise is largest at small separation and
   falls with distance — opposite to the hypothesised trend.  The angle
   between the two segments is returned so the curve can be stratified by
   conditioning, and the real-photo control curve carries the same confound.

2. `windowed_locality` — estimate VPs independently inside image windows and
   measure how much window-local VPs disagree with each other versus the
   distance between window centres.  Closer to the sheaf formulation (§4.4):
   windows are local sections, agreement on overlaps is the gluing condition.
"""

from __future__ import annotations

import numpy as np

from .camera import vp_rays
from .geometry import unit
from .lines import Segments
from .vp import VPResult, estimate_vps


def _ray_angle_deg(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    c = np.clip(np.abs(np.sum(unit(a) * unit(b), axis=-1)), 0, 1)
    return np.degrees(np.arccos(c))


def pairwise_locality(segs: Segments, vpr: VPResult, f: float, width: int, height: int,
                      max_pairs_per_vp: int = 3000, seed: int = 0) -> dict:
    """Returns arrays over sampled same-VP segment pairs:
    dist (midpoint distance / image diagonal), disagreement (deg, ray space),
    pair_angle (deg between the two segments; small = ill-conditioned), vp (id)."""
    rng = np.random.default_rng(seed)
    pp = np.array([width / 2.0, height / 2.0])
    diag = float(np.hypot(width, height))
    L = segs.lines
    M = segs.midpoints
    D = segs.directions
    out = {"dist": [], "disagreement": [], "pair_angle": [], "vp": []}
    for k, v in enumerate(vpr.vps):
        idx = np.flatnonzero(vpr.labels == k)
        if idx.size < 4:
            continue
        n_pairs = idx.size * (idx.size - 1) // 2
        if n_pairs <= max_pairs_per_vp:
            ii, jj = np.triu_indices(idx.size, k=1)
        else:
            ii = rng.integers(0, idx.size, max_pairs_per_vp)
            jj = rng.integers(0, idx.size, max_pairs_per_vp)
            keep = ii != jj
            ii, jj = ii[keep], jj[keep]
        a, b = idx[ii], idx[jj]
        p = np.cross(L[a], L[b])                       # local two-line VP
        gr = vp_rays(v[None], f, pp)[0]
        pr = vp_rays(p, f, pp)
        out["disagreement"].append(_ray_angle_deg(pr, gr[None]))
        out["dist"].append(np.linalg.norm(M[a] - M[b], axis=1) / diag)
        c = np.clip(np.abs(np.sum(D[a] * D[b], axis=1)), 0, 1)
        out["pair_angle"].append(np.degrees(np.arccos(c)))
        out["vp"].append(np.full(a.size, k))
    return {k: (np.concatenate(v) if v else np.zeros(0)) for k, v in out.items()}


def bin_curve(dist: np.ndarray, val: np.ndarray, edges: np.ndarray, stat=np.nanmedian) -> np.ndarray:
    """Per-bin statistic of `val` over `dist` bins (nan where empty)."""
    out = np.full(len(edges) - 1, np.nan)
    which = np.digitize(dist, edges) - 1
    for b in range(len(edges) - 1):
        m = which == b
        if m.sum() >= 5:
            out[b] = stat(val[m])
    return out


def windowed_locality(segs: Segments, vpr: VPResult, f: float, width: int, height: int,
                      grid: int = 2, min_segments: int = 25, thresh_deg: float = 2.0) -> dict:
    """Estimate VPs inside each grid cell from that cell's segments only, match
    them to the global VPs (by ray angle at the global f) and return, for every
    pair of cells that both recovered a given global VP, the distance between
    cell centres (/diag) and the ray-space disagreement of their local VPs."""
    pp = np.array([width / 2.0, height / 2.0])
    diag = float(np.hypot(width, height))
    M = segs.midpoints
    G = vp_rays(vpr.vps, f, pp)
    cells = []
    for gy in range(grid):
        for gx in range(grid):
            x0, x1 = gx * width / grid, (gx + 1) * width / grid
            y0, y1 = gy * height / grid, (gy + 1) * height / grid
            m = (M[:, 0] >= x0) & (M[:, 0] < x1) & (M[:, 1] >= y0) & (M[:, 1] < y1)
            if m.sum() < min_segments:
                continue
            local = estimate_vps(segs[m], width, height, n_vps=len(vpr.vps),
                                 thresh_deg=thresh_deg, n_iter=300)
            if len(local.vps) == 0:
                continue
            R = vp_rays(local.vps, f, pp)
            ang = np.degrees(np.arccos(np.clip(np.abs(R @ G.T), 0, 1)))   # (local, global)
            match = {}
            for k in range(len(G)):
                j = int(ang[:, k].argmin())
                if ang[j, k] < 10 and int(ang[j].argmin()) == k:
                    match[k] = R[j]
            cells.append({"centre": np.array([(x0 + x1) / 2, (y0 + y1) / 2]),
                          "match": match, "local_err": {k: float(ang[:, k].min()) for k in range(len(G))}})
    dist, dis, vp = [], [], []
    for i in range(len(cells)):
        for j in range(i + 1, len(cells)):
            for k in cells[i]["match"].keys() & cells[j]["match"].keys():
                dist.append(np.linalg.norm(cells[i]["centre"] - cells[j]["centre"]) / diag)
                dis.append(_ray_angle_deg(cells[i]["match"][k], cells[j]["match"][k]))
                vp.append(k)
    return {"dist": np.array(dist), "disagreement": np.array(dis), "vp": np.array(vp),
            "n_cells": len(cells),
            "local_vs_global": np.array([c["local_err"][k] for c in cells for k in c["local_err"]])}


def consistent_twin(segs: Segments, vpr: VPResult, seed: int = 0,
                    noise_deg: float | None = None) -> Segments:
    """Conditioning-matched null: re-aim every inlier segment exactly at its
    global VP (same midpoint and length) and add angular noise matched to the
    image's own inlier residual level.  The twin has the same line layout as
    the image but satisfies the single-camera hypothesis by construction, so
    any locality statistic computed on image minus twin is free of the
    conditioning confound.  Outliers are left untouched."""
    rng = np.random.default_rng(seed)
    xy = segs.xy.copy()
    mid = segs.midpoints
    L = segs.lengths
    for k, v in enumerate(vpr.vps):
        m = vpr.labels == k
        if not m.any():
            continue
        if noise_deg is None:
            r = vpr.residuals[m]
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


def locality_excess(segs: Segments, vpr: VPResult, f: float, width: int, height: int,
                    edges: np.ndarray, grid: int = 3, n_twins: int = 3,
                    min_pair_angle: float = 3.0, seed: int = 0) -> dict:
    """Image-minus-twin locality curves (pairwise and windowed).  Twin curves
    are averaged over `n_twins` noise draws.  Returns per-bin arrays."""
    pw = pairwise_locality(segs, vpr, f, width, height, seed=seed)
    ok = pw["pair_angle"] > min_pair_angle
    pw_img = bin_curve(pw["dist"][ok], pw["disagreement"][ok], edges)
    wl = windowed_locality(segs, vpr, f, width, height, grid=grid)
    wl_img = bin_curve(wl["dist"], wl["disagreement"], edges)
    pw_tw, wl_tw = [], []
    for t in range(n_twins):
        twin = consistent_twin(segs, vpr, seed=seed + t)
        p = pairwise_locality(twin, vpr, f, width, height, seed=seed)
        ok = p["pair_angle"] > min_pair_angle
        pw_tw.append(bin_curve(p["dist"][ok], p["disagreement"][ok], edges))
        w = windowed_locality(twin, vpr, f, width, height, grid=grid)
        wl_tw.append(bin_curve(w["dist"], w["disagreement"], edges))
    pw_tw = np.nanmean(pw_tw, axis=0)
    wl_tw = np.nanmean(wl_tw, axis=0)
    return {"edges": edges, "pairwise_img": pw_img, "pairwise_twin": pw_tw,
            "pairwise_excess": pw_img - pw_tw,
            "windowed_img": wl_img, "windowed_twin": wl_tw, "windowed_excess": wl_img - wl_tw,
            "n_window_pairs": int(wl["dist"].size)}


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
                       cap_deg: float = 10.0) -> dict:
    """Semivariogram of signed residuals over same-VP inlier pairs.

    gamma(d) = 1/2 E[(r_i - r_j)^2 | dist = d], normalised by the residual
    variance so that independent residuals give gamma = 1 at every distance.
    rho(d) = 1 - gamma(d) is the spatial correlation: > 0 at short range and
    < 0 at long range means "locally consistent, globally inconsistent".
    Also returns the pooled correlation for near (< edges[2]) vs far pairs.

    Uses the *uncensored* nearest-VP assignment (every segment within
    `cap_deg` of its nearest VP) so that large, smooth drifts are not thrown
    out by the tight inlier threshold used for VP estimation."""
    rng = np.random.default_rng(seed)
    diag = float(np.hypot(width, height))
    M = segs.midpoints
    dist, sq, var_w = [], [], []
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
        dist.append(np.linalg.norm(M[idx[ii]] - M[idx[jj]], axis=1) / diag)
        sq.append(0.5 * (r[ii] - r[jj]) ** 2 / var)
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
