"""L3: camera coherence from three vanishing points.

Claim under test: the three dominant VPs are images of mutually orthogonal
3D directions seen through a pinhole camera with square pixels, zero skew and
principal point at the image centre.  Under that claim there is a focal
length f such that the back-projected rays K^-1 v_i are pairwise orthogonal.

We report
  * per-pair closed-form focal estimates  f^2 = -(v_i - p).(v_j - p)
    (negative f^2 = impossible configuration),
  * the single best-fit f (and the resulting field of view),
  * the pairwise orthogonality error in degrees at that f  <- main residual,
  * the orthocentre of the VP triangle and its offset from the image centre.

Everything works with homogeneous VPs, so VPs at infinity are handled.
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import minimize_scalar

from .geometry import to_inhomogeneous, unit


def vp_rays(vps: np.ndarray, f: float, pp: np.ndarray) -> np.ndarray:
    """Unit 3D direction of each VP for camera K = [f 0 px; 0 f py; 0 0 1]."""
    vps = np.asarray(vps, dtype=float)
    Kinv = np.array([[1 / f, 0, -pp[0] / f], [0, 1 / f, -pp[1] / f], [0, 0, 1.0]])
    return unit(vps @ Kinv.T)


def _is_infinite(v: np.ndarray, max_px: float = 1e7) -> bool:
    return abs(v[2]) * max_px < np.linalg.norm(v[:2])


def pairwise_focal(vps: np.ndarray, pp: np.ndarray) -> list[dict]:
    """Closed-form f^2 from each VP pair.  Uses homogeneous coordinates:
    f^2 w_i w_j = -[(x_i - px w_i)(x_j - px w_j) + (y_i - py w_i)(y_j - py w_j)].
    A pair with one VP at infinity gives no focal constraint."""
    vps = np.asarray(vps, dtype=float)
    out = []
    K = len(vps)
    for i in range(K):
        for j in range(i + 1, K):
            vi, vj = vps[i], vps[j]
            num = -((vi[0] - pp[0] * vi[2]) * (vj[0] - pp[0] * vj[2])
                    + (vi[1] - pp[1] * vi[2]) * (vj[1] - pp[1] * vj[2]))
            # "at infinity" = further than 1e7 px from the origin
            if _is_infinite(vi) or _is_infinite(vj):
                out.append({"pair": (i, j), "f2": None, "f": None, "at_infinity": True})
                continue
            f2 = num / (vi[2] * vj[2])
            out.append({"pair": (i, j), "f2": float(f2),
                        "f": float(np.sqrt(f2)) if f2 > 0 else None,
                        "at_infinity": False})
    return out


def orthogonality_errors(vps: np.ndarray, f: float, pp: np.ndarray) -> np.ndarray:
    """|90 - angle(r_i, r_j)| in degrees for every VP pair."""
    r = vp_rays(vps, f, pp)
    K = len(r)
    errs = []
    for i in range(K):
        for j in range(i + 1, K):
            c = np.clip(abs(r[i] @ r[j]), 0, 1)
            errs.append(90.0 - np.degrees(np.arccos(c)))
    return np.array(errs)


def fit_focal(vps: np.ndarray, pp: np.ndarray, diag: float) -> float:
    """Best single f (pixels): minimizes sum of squared cosines between rays.
    Search over log f in [0.1, 20] x image diagonal."""
    def cost(logf):
        r = vp_rays(vps, np.exp(logf), pp)
        K = len(r)
        return sum((r[i] @ r[j]) ** 2 for i in range(K) for j in range(i + 1, K))

    res = minimize_scalar(cost, bounds=(np.log(0.1 * diag), np.log(20 * diag)), method="bounded")
    return float(np.exp(res.x))


def orthocenter(vps: np.ndarray):
    """Orthocentre of the triangle of three finite VPs, else None."""
    pts = [to_inhomogeneous(v) for v in vps]
    if len(pts) != 3 or any(p is None for p in pts):
        return None
    a, b, c = pts
    # altitude from a: through a, perpendicular to (c - b); from b: perp to (c - a)
    A = np.stack([c - b, c - a])
    rhs = np.array([(c - b) @ a, (c - a) @ b])
    if abs(np.linalg.det(A)) < 1e-9:
        return None
    return np.linalg.solve(A, rhs)


def l3_report(vps: np.ndarray, width: int, height: int) -> dict:
    """Camera-coherence residuals for up to three VPs."""
    vps = np.asarray(vps, dtype=float)
    pp = np.array([width / 2.0, height / 2.0])
    diag = float(np.hypot(width, height))
    rep: dict = {"n_vps": int(len(vps)), "principal_point": pp.tolist()}
    if len(vps) < 2:
        rep["status"] = "insufficient_vps"
        return rep

    pf = pairwise_focal(vps, pp)
    rep["pairwise_focal"] = pf
    rep["n_negative_f2"] = int(sum(1 for d in pf if d["f2"] is not None and d["f2"] <= 0))
    f = fit_focal(vps, pp, diag)
    rep["f_fit"] = f
    rep["hfov_deg"] = float(2 * np.degrees(np.arctan(width / (2 * f))))
    errs = orthogonality_errors(vps, f, pp)
    rep["ortho_err_deg"] = errs.tolist()
    rep["ortho_err_max_deg"] = float(errs.max())
    rep["ortho_err_rms_deg"] = float(np.sqrt((errs ** 2).mean()))
    finite_f = [d["f"] for d in pf if d["f"] is not None]
    rep["f_spread"] = float(np.std(finite_f) / np.mean(finite_f)) if len(finite_f) >= 2 else None

    oc = orthocenter(vps) if len(vps) == 3 else None
    if oc is not None:
        rep["orthocenter"] = oc.tolist()
        rep["orthocenter_offset"] = float(np.linalg.norm(oc - pp) / diag)
    else:
        rep["orthocenter"] = None
        rep["orthocenter_offset"] = None
    rep["status"] = "ok"
    return rep
