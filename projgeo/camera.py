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


def l3_uncertainty(vps: np.ndarray, samples: np.ndarray, width: int, height: int,
                   f: float | None = None) -> dict:
    """Bootstrap uncertainty of the L3 residuals.

    `samples` is (B, K, 3) from `vp.bootstrap_vps`.  Reports each VP's angular
    std in ray space (at the fitted f) and the std / 95th percentile of the
    ortho-error statistics over the bootstrap replicates.
    """
    pp = np.array([width / 2.0, height / 2.0])
    diag = float(np.hypot(width, height))
    if f is None:
        f = fit_focal(vps, pp, diag)
    r0 = vp_rays(vps, f, pp)
    B, K, _ = samples.shape
    vp_std = np.zeros(K)
    for k in range(K):
        rk = vp_rays(samples[:, k], f, pp)
        ang = np.degrees(np.arccos(np.clip(np.abs(rk @ r0[k]), 0, 1)))
        vp_std[k] = float(np.sqrt(np.mean(ang ** 2)))
    boot_max, boot_rms, boot_f = [], [], []
    if K >= 2:
        for b in range(B):
            fb = fit_focal(samples[b], pp, diag)
            e = orthogonality_errors(samples[b], fb, pp)
            boot_max.append(e.max()); boot_rms.append(np.sqrt((e ** 2).mean())); boot_f.append(fb)
    boot_max = np.array(boot_max); boot_f = np.array(boot_f)
    return {
        "n_boot": int(B),
        "vp_std_deg": vp_std.tolist(),
        "vp_std_max_deg": float(vp_std.max()) if K else None,
        "ortho_err_max_boot_std": float(boot_max.std()) if K >= 2 else None,
        "ortho_err_max_boot_p95": float(np.percentile(boot_max, 95)) if K >= 2 else None,
        "f_boot_cv": float(boot_f.std() / boot_f.mean()) if K >= 2 else None,
    }


def select_manhattan_triple(vps: np.ndarray, width: int, height: int,
                            support: np.ndarray | None = None, min_support_frac: float = 0.04) -> dict:
    """Model selection over VP candidates (plan 4.6, simplified).

    Among up to K candidate VPs choose the triple whose back-projected rays are
    closest to mutually orthogonal for the best single focal length (principal
    point at the image centre).  Returns the chosen indices and its L3 report,
    plus the best pair when no triple exists.  A third VP that is a genuine but
    non-orthogonal 3D direction (roof pitch, diagonal street) is thereby
    ignored instead of being scored as a camera failure.
    """
    from itertools import combinations
    K = len(vps)
    idx = list(range(K))
    if support is not None and K:
        tot = float(np.sum(support))
        idx = [i for i in idx if support[i] / max(tot, 1e-9) >= min_support_frac]
    best = None
    for tri in combinations(idx, 3):
        rep = l3_report(vps[list(tri)], width, height)
        if rep.get("status") != "ok":
            continue
        if best is None or rep["ortho_err_max_deg"] < best["ortho_err_max_deg"]:
            best = {**rep, "triple": list(tri)}
    if best is not None:
        best["model"] = "M3"
        return best
    for pair in combinations(idx, 2):
        rep = l3_report(vps[list(pair)], width, height)
        if rep.get("status") != "ok":
            continue
        if best is None or rep["ortho_err_max_deg"] < best["ortho_err_max_deg"]:
            best = {**rep, "triple": list(pair)}
    if best is not None:
        best["model"] = "M2"
        return best
    return {"status": "insufficient_vps", "model": "M0", "triple": []}


def atlanta_focal_consistency(vps: np.ndarray, support: np.ndarray, width: int, height: int,
                              min_support_frac: float = 0.04, vert_tol_deg: float = 30.0,
                              min_vert_dist: float = 0.0) -> dict:
    """L3 for Atlanta worlds (plan 4.6): several horizontal directions, one
    vertical.  Every horizontal VP is orthogonal to the vertical one, so each
    (horizontal, vertical) pair implies a focal length via
    f^2 = -(v_h - p).(v_v - p); a real camera makes them agree.

    The vertical VP is the best-supported candidate whose direction from the
    image centre is within `vert_tol_deg` of the image y-axis (identified by
    direction only, never by orthogonality).  Returns the per-pair focal
    estimates, the fraction with f^2 <= 0 (impossible pairs) and the spread
    of log f over the possible pairs.

    `min_vert_dist` (pixels) also requires the vertical VP to lie at least that
    far from the image centre.  A VP near the centre (the depth VP of a
    corridor or street seen head-on) has an arbitrary direction from the
    centre and can pass the direction test by accident; a true vertical VP is
    only that close for a camera pitched steeply up or down.  Uses position
    only, never orthogonality or f, so it keeps the rule non-circular.
    Default 0 = original behaviour (plan 7.25).
    """
    pp = np.array([width / 2.0, height / 2.0])
    tot = float(np.sum(support)) if len(support) else 1.0
    cand = [i for i in range(len(vps)) if support[i] / max(tot, 1e-9) >= min_support_frac]
    vert = None
    for i in sorted(cand, key=lambda i: -support[i]):
        v = vps[i]
        d = v[:2] - pp * v[2]            # direction from centre (works at infinity)
        if min_vert_dist > 0 and abs(v[2]) > 1e-12 and np.hypot(*(d / v[2])) < min_vert_dist:
            continue
        ang = np.degrees(np.arctan2(abs(d[0]), abs(d[1])))   # 0 = vertical
        if ang < vert_tol_deg:
            vert = i
            break
    out = {"vertical": vert, "pairs": [], "n_pairs": 0, "frac_impossible": np.nan,
           "logf_spread": np.nan, "f_median": np.nan}
    if vert is None:
        return out
    fs = []
    for i in cand:
        if i == vert:
            continue
        pf = pairwise_focal(vps[[i, vert]], pp)[0]
        out["pairs"].append({"h": i, "f2": pf["f2"], "f": pf["f"]})
        if pf["f2"] is not None:
            fs.append(pf["f2"])
    fs = np.array(fs)
    out["n_pairs"] = int(len(fs))
    if len(fs):
        out["frac_impossible"] = float(np.mean(fs <= 0))
        pos = fs[fs > 0]
        if len(pos):
            out["f_median"] = float(np.sqrt(np.median(pos)))
        if len(pos) >= 2:
            lf = 0.5 * np.log(pos)
            out["logf_spread"] = float(lf.max() - lf.min())
    return out
