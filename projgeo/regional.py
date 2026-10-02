"""Regional camera consistency (plan 4.4 / 7.9): does every part of the image
imply the same camera?

Each window U_i of an overlapping grid gets its own unconstrained camera
estimate (VPs + focal length, principal point fixed at the image centre).
Windows are the open sets of a cover, local cameras are the sections, and
because a camera is a global object the restriction maps are identities, so

  * pairwise disagreement d(s_i, s_j) between windows measures failure to
    glue on overlaps (the sheaf-Laplacian energy is the sum of squares), and
  * the consistency radius is the smallest eps such that one global camera
    is within eps of every local section (a min-max fit).

Camera distance has two components: the rotation angle between the VP frames
(deg) and |log f_i / f_j|.  Both are reported separately.

Caveat (plan 7.24): each window's focal length comes from
`camera.fit_focal`, which assumes all the window's VPs are mutually
perpendicular.  That holds on York Urban by construction but is unverified on
Atlanta-world scenes, so this analysis is reported but not counted as
independent evidence.
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import minimize
from scipy.spatial.transform import Rotation

from .camera import fit_focal, vp_rays
from .geometry import unit
from .lines import Segments
from .vp import VPResult, estimate_vps


def _frame_from_rays(rays_local: np.ndarray, rays_ref: np.ndarray) -> np.ndarray | None:
    """Rotation R (3x3) minimising sum |R g_k - r_k|^2 over matched VP rays,
    with the sign of each local ray flipped to agree with the reference
    (VPs are directions up to sign).  Needs >= 2 matched rays."""
    if len(rays_local) < 2:
        return None
    r = rays_local * np.sign(np.sum(rays_local * rays_ref, axis=1, keepdims=True) + 1e-12)
    g = rays_ref
    if len(r) == 2:  # complete both frames with the cross product
        r = np.vstack([r, unit(np.cross(r[0], r[1]))])
        g = np.vstack([g, unit(np.cross(g[0], g[1]))])
    H = g.T @ r
    U, _, Vt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    D = np.diag([1, 1, d])
    return Vt.T @ D @ U.T


def window_grid(width: int, height: int, n: int = 3, frac: float = 0.5):
    """n x n windows of size frac*(w,h) with equal stride, as (x0, y0, x1, y1)."""
    ww, wh = frac * width, frac * height
    xs = np.linspace(0, width - ww, n)
    ys = np.linspace(0, height - wh, n)
    return [(x, y, x + ww, y + wh) for y in ys for x in xs]


def regional_cameras(segs: Segments, vpr: VPResult, f_global: float, width: int, height: int,
                     n: int = 3, frac: float = 0.5, min_segments: int = 40,
                     min_support_frac: float = 0.05, match_deg: float = 15.0,
                     thresh_deg: float = 2.0) -> dict:
    """Fit a camera in each window and compare.

    Returns per-window records (centre, f, rotation relative to the global
    frame, matched VP ids) and summary statistics:
      rot_pairwise_deg  : median rotation angle between window frames (all pairs)
      rot_adjacent_deg  : same, adjacent windows only (overlap = gluing condition)
      logf_pairwise     : median |log f_i/f_j| over all pairs
      radius_rot_deg    : min over R of max_i angle(R_i, R)   (consistency radius)
      radius_logf       : min over f of max_i |log f_i/f| = half the log-range
      n_windows         : windows with a valid camera
    """
    pp = np.array([width / 2.0, height / 2.0])
    diag = float(np.hypot(width, height))
    G = vp_rays(vpr.vps, f_global, pp)
    M = segs.midpoints
    wins = window_grid(width, height, n, frac)
    recs = []
    for wi, (x0, y0, x1, y1) in enumerate(wins):
        m = (M[:, 0] >= x0) & (M[:, 0] < x1) & (M[:, 1] >= y0) & (M[:, 1] < y1)
        if m.sum() < min_segments:
            continue
        sub = segs[m]
        loc = estimate_vps(sub, width, height, n_vps=len(vpr.vps), thresh_deg=thresh_deg, n_iter=300)
        if len(loc.vps) < 2:
            continue
        keep = loc.support / max(sub.lengths.sum(), 1e-9) >= min_support_frac
        if keep.sum() < 2:
            continue
        lv = loc.vps[keep]
        f_loc = fit_focal(lv, pp, diag)
        R_loc = vp_rays(lv, f_loc, pp)
        ang = np.degrees(np.arccos(np.clip(np.abs(R_loc @ G.T), 0, 1)))   # (local, global)
        matched, rays = [], []
        for k in range(len(G)):
            j = int(ang[:, k].argmin())
            if ang[j, k] < match_deg and int(ang[j].argmin()) == k:
                matched.append(k)
                rays.append(R_loc[j])
        if len(matched) < 2:
            continue
        Rm = _frame_from_rays(np.array(rays), G[matched])
        if Rm is None:
            continue
        recs.append({"window": wi, "centre": np.array([(x0 + x1) / 2, (y0 + y1) / 2]),
                     "f": f_loc, "R": Rm, "matched": matched, "n_segments": int(m.sum())})

    out = {"windows": recs, "n_windows": len(recs)}
    if len(recs) < 2:
        out.update({k: np.nan for k in ("rot_pairwise_deg", "rot_adjacent_deg", "logf_pairwise",
                                         "radius_rot_deg", "radius_logf", "rot_vs_dist")})
        return out

    Rs = [r["R"] for r in recs]
    logf = np.log([r["f"] for r in recs])
    C = np.array([r["centre"] for r in recs])
    rot, lf, dist, adj = [], [], [], []
    stride = np.array([width, height]) * (1 - frac) / max(n - 1, 1)
    for i in range(len(recs)):
        for j in range(i + 1, len(recs)):
            a = np.degrees(Rotation.from_matrix(Rs[i] @ Rs[j].T).magnitude())
            rot.append(a)
            lf.append(abs(logf[i] - logf[j]))
            d = np.abs(C[i] - C[j])
            dist.append(np.linalg.norm(C[i] - C[j]) / diag)
            adj.append(bool((d <= stride * 1.01).all()))
    rot, lf, dist, adj = map(np.array, (rot, lf, dist, adj))

    # consistency radius: one global rotation minimising the max distance
    def maxdist(rv):
        R = Rotation.from_rotvec(rv).as_matrix()
        return max(np.degrees(Rotation.from_matrix(Ri @ R.T).magnitude()) for Ri in Rs)
    mean_rv = Rotation.from_matrix(np.array(Rs)).mean().as_rotvec()
    res = minimize(maxdist, mean_rv, method="Nelder-Mead", options={"xatol": 1e-4, "fatol": 1e-3, "maxiter": 400})
    radius_rot = float(min(res.fun, maxdist(mean_rv)))

    out.update({
        "rot_pairwise_deg": float(np.median(rot)),
        "rot_adjacent_deg": float(np.median(rot[adj])) if adj.any() else np.nan,
        "logf_pairwise": float(np.median(lf)),
        "radius_rot_deg": radius_rot,
        "radius_logf": float(0.5 * (logf.max() - logf.min())),
        "rot_vs_dist": np.stack([dist, rot], axis=1),
    })
    return out
