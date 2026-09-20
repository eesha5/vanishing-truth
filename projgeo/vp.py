"""Vanishing-point estimation and the L2 (concurrency) residual.

Estimation is deliberately *unconstrained*: VPs are found one at a time by
RANSAC + angular least squares without any Manhattan / orthogonality prior.
Whether the recovered VPs are consistent with a single pinhole camera is the
question L3 asks, so the estimator must not assume the answer.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.optimize import least_squares

from .geometry import hom, line_direction, normalizing_transform, unit
from .lines import Segments


def angular_residuals(segs: Segments, vp: np.ndarray) -> np.ndarray:
    """Per-segment angle (deg) between the segment and the line joining its
    midpoint to `vp`.  Works for VPs at infinity (vp[2] == 0)."""
    M = hom(segs.midpoints)
    ideal = np.cross(M, np.asarray(vp, dtype=float)[None, :])
    d_ideal = line_direction(ideal)
    c = np.abs(np.sum(segs.directions * d_ideal, axis=1))
    return np.degrees(np.arccos(np.clip(c, 0.0, 1.0)))


def _sph_to_vec(t: np.ndarray) -> np.ndarray:
    th, ph = t
    return np.array([np.sin(th) * np.cos(ph), np.sin(th) * np.sin(ph), np.cos(th)])


def _vec_to_sph(v: np.ndarray) -> np.ndarray:
    v = unit(v)
    return np.array([np.arccos(np.clip(v[2], -1, 1)), np.arctan2(v[1], v[0])])


def refine_vp(segs: Segments, vp0: np.ndarray, weights: np.ndarray | None = None) -> np.ndarray:
    """Minimize weighted angular residuals over the unit sphere."""
    if len(segs) < 2:
        return unit(vp0)
    w = np.sqrt(weights) if weights is not None else np.ones(len(segs))

    def fun(t):
        return w * angular_residuals(segs, _sph_to_vec(t))

    res = least_squares(fun, _vec_to_sph(vp0), method="lm", max_nfev=200)
    return _sph_to_vec(res.x)


def ransac_vp(segs: Segments, thresh_deg: float = 2.0, n_iter: int = 500,
              rng: np.random.Generator | None = None):
    """Single-VP RANSAC in the given coordinates.  Returns (vp, inlier_mask, score)."""
    rng = rng or np.random.default_rng(0)
    n = len(segs)
    if n < 2:
        return None, np.zeros(n, bool), 0.0
    L = segs.lines
    lengths = segs.lengths
    p = lengths / lengths.sum()
    best_score, best_vp, best_in = -1.0, None, None
    for _ in range(n_iter):
        i, j = rng.choice(n, size=2, replace=False, p=p)
        v = np.cross(L[i], L[j])
        if np.linalg.norm(v) < 1e-12:
            continue
        r = angular_residuals(segs, v)
        inl = r < thresh_deg
        score = lengths[inl].sum()
        if score > best_score:
            best_score, best_vp, best_in = score, v, inl
    if best_vp is None:
        return None, np.zeros(n, bool), 0.0
    vp = refine_vp(segs[best_in], best_vp, lengths[best_in])
    inl = angular_residuals(segs, vp) < thresh_deg
    vp = refine_vp(segs[inl], vp, lengths[inl])
    inl = angular_residuals(segs, vp) < thresh_deg
    return vp, inl, float(lengths[inl].sum())


@dataclass
class VPResult:
    vps: np.ndarray                 # (K,3) homogeneous, pixel coordinates, unit norm
    labels: np.ndarray              # (N,) cluster id per segment, -1 = outlier
    residuals: np.ndarray           # (N,) angular residual to assigned VP (nan for outliers)
    support: np.ndarray             # (K,) total inlier length per VP
    thresh_deg: float
    nearest: np.ndarray = None      # (N,) nearest VP id for every segment (uncensored)
    residuals_all: np.ndarray = None  # (N,) residual to nearest VP, uncensored
    lengths: np.ndarray = None      # (N,) segment lengths (px)
    meta: dict = field(default_factory=dict)

    def l2_summary(self) -> dict:
        out = {}
        for k in range(len(self.vps)):
            m = self.labels == k
            r = self.residuals[m]
            out[k] = {
                "n": int(m.sum()),
                "support": float(self.support[k]),
                "mean_deg": float(r.mean()) if m.any() else float("nan"),
                "median_deg": float(np.median(r)) if m.any() else float("nan"),
                "rms_deg": float(np.sqrt((r ** 2).mean())) if m.any() else float("nan"),
            }
        r_all = self.residuals[self.labels >= 0]
        out["all"] = {
            "n": int((self.labels >= 0).sum()),
            "n_outliers": int((self.labels < 0).sum()),
            "mean_deg": float(r_all.mean()) if r_all.size else float("nan"),
            "rms_deg": float(np.sqrt((r_all ** 2).mean())) if r_all.size else float("nan"),
        }
        # Uncensored statistics: inlier RMS saturates at the threshold, so we
        # also report how much line length no VP explains, and a capped
        # residual over *every* segment (Huber-like, cap = 5 x threshold).
        if self.residuals_all is not None and self.residuals_all.size:
            w = self.lengths / self.lengths.sum()
            cap = cap_deg if (cap_deg := 5 * self.thresh_deg) else 10.0
            r = np.minimum(self.residuals_all, cap)
            out["all"]["unexplained_frac"] = float(w[self.residuals_all >= self.thresh_deg].sum())
            out["all"]["capped_mean_deg"] = float((w * r).sum())
            out["all"]["cap_deg"] = float(cap)
        return out


def estimate_vps(segs: Segments, width: int, height: int, n_vps: int = 3,
                 thresh_deg: float = 2.0, n_iter: int = 500, min_support: int = 5,
                 seed: int = 0) -> VPResult:
    """Sequential unconstrained VP estimation.

    Segments are mapped to normalized coordinates, VPs are found one at a
    time (largest length-weighted support first), each VP's inliers are
    removed, and finally every segment is assigned to its best VP if within
    `thresh_deg`.  VPs are returned in pixel homogeneous coordinates.
    """
    rng = np.random.default_rng(seed)
    T = normalizing_transform(width, height)
    S = segs.transformed(T)
    n = len(S)
    remaining = np.ones(n, bool)
    vps_norm = []
    for _ in range(n_vps):
        idx = np.flatnonzero(remaining)
        if idx.size < max(2, min_support):
            break
        vp, inl, _ = ransac_vp(S[idx], thresh_deg, n_iter, rng)
        if vp is None or inl.sum() < min_support:
            break
        vps_norm.append(vp)
        remaining[idx[inl]] = False

    K = len(vps_norm)
    labels = -np.ones(n, int)
    resid = np.full(n, np.nan)
    support = np.zeros(K)
    if K:
        R = np.stack([angular_residuals(S, v) for v in vps_norm], axis=1)  # (N,K)
        best = R.argmin(axis=1)
        bestr = R[np.arange(n), best]
        ok = bestr < thresh_deg
        labels[ok] = best[ok]
        resid[ok] = bestr[ok]
        # one joint re-refinement with final assignments
        for k in range(K):
            m = labels == k
            if m.sum() >= 2:
                vps_norm[k] = refine_vp(S[m], vps_norm[k], S.lengths[m])
        R = np.stack([angular_residuals(S, v) for v in vps_norm], axis=1)
        best = R.argmin(axis=1)
        bestr = R[np.arange(n), best]
        ok = bestr < thresh_deg
        labels[:] = -1
        labels[ok] = best[ok]
        resid[:] = np.nan
        resid[ok] = bestr[ok]
        for k in range(K):
            support[k] = segs.lengths[labels == k].sum()
        nearest, resid_all = best.copy(), bestr.copy()
    else:
        nearest, resid_all = -np.ones(n, int), np.full(n, np.nan)

    # back to pixel coordinates: v_pix = T^{-1} v_norm
    Tinv = np.linalg.inv(T)
    vps_pix = unit(np.stack([Tinv @ v for v in vps_norm], axis=0)) if K else np.zeros((0, 3))
    # order by support
    order = np.argsort(-support)
    remap = {old: new for new, old in enumerate(order)}
    labels = np.array([remap.get(l, -1) if l >= 0 else -1 for l in labels])
    nearest = np.array([remap.get(l, -1) if l >= 0 else -1 for l in nearest])
    return VPResult(vps=vps_pix[order], labels=labels, residuals=resid,
                    support=support[order], thresh_deg=thresh_deg,
                    nearest=nearest, residuals_all=resid_all, lengths=segs.lengths,
                    meta={"width": width, "height": height})


def bootstrap_vps(segs: Segments, vpr: VPResult, B: int = 30, seed: int = 0) -> np.ndarray:
    """Resample each VP's inlier segments with replacement and re-refine.

    Returns (B, K, 3) homogeneous VP samples in pixel coordinates.  The spread
    of the samples measures how well the lines actually pin the VP down
    (near-parallel families give VPs that slide along their direction), so
    downstream residuals can be compared with their own uncertainty.
    """
    rng = np.random.default_rng(seed)
    w, h = vpr.meta["width"], vpr.meta["height"]
    T = normalizing_transform(w, h)
    Tinv = np.linalg.inv(T)
    S = segs.transformed(T)
    K = len(vpr.vps)
    out = np.zeros((B, K, 3))
    for k in range(K):
        idx = np.flatnonzero(vpr.labels == k)
        v0 = unit(T @ vpr.vps[k])
        if idx.size < 2:
            out[:, k] = vpr.vps[k]
            continue
        for b in range(B):
            bs = rng.choice(idx, size=idx.size, replace=True)
            v = refine_vp(S[bs], v0, S.lengths[bs])
            out[b, k] = unit(Tinv @ v)
    return out
