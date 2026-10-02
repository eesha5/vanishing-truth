"""L7: shadow consistency via wedge constraints (Kee, O'Brien & Farid, TOG 2013).

Geometry.  Under a single light source, a point on a cast shadow and the point
on the object that cast it are joined by a line that passes through the image
of the light.  If a shadow point `s` is only known to correspond to *somewhere*
on an object region, the constraint becomes a **wedge**: the light's image must
lie in the cone spanned, at `s`, by the extreme rays to that region.  A wedge is
the intersection of two half-planes, so "do all constraints admit one light?"
is a linear feasibility problem.

Residual.  We do not just return feasible / infeasible: the LP minimises the
largest half-plane violation `t` (in pixels, because the half-plane normals are
unit vectors).  `t <= 0` means a consistent light exists with margin `-t`;
`t > 0` is how far the constraints are from admitting any light, which is the
interpretable residual this project wants.

The light may be finite (sun in frame, lamp) or effectively at infinity
(parallel rays).  Rather than a separate projective branch, `L` is simply
bounded by a large multiple of the image diagonal: at image precision a light
50 diagonals away is indistinguishable from one at infinity, and the LP stays
in pixel units throughout.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import linprog


@dataclass
class ShadowPair:
    """One shadow point and the object region it may have come from.

    `shadow` is a 2D image point on the cast shadow.  `object_a` / `object_b`
    are the extreme points of the corresponding object region (they may be
    equal for an exact correspondence).  The light lies on the far side of the
    object from the shadow, inside the wedge at `shadow` spanned by the two
    rays.
    """

    shadow: np.ndarray
    object_a: np.ndarray
    object_b: np.ndarray
    label: str = ""

    def __post_init__(self):
        self.shadow = np.asarray(self.shadow, float)
        self.object_a = np.asarray(self.object_a, float)
        self.object_b = np.asarray(self.object_b, float)

    def half_planes(self) -> np.ndarray:
        """Two rows (a1, a2, b) with |(a1, a2)| = 1 encoding a.L <= b.

        The wedge at `shadow` spanned by the rays towards `object_a` and
        `object_b` (and continuing past them) is the intersection of the two
        half-planes whose boundaries are those rays and which both contain the
        wedge interior.
        """
        s = self.shadow
        # Degenerate (exact) correspondence: the wedge has zero width, so the
        # light must lie *on* the line through s and the object point.  Two
        # opposing half-planes express that equality, and the LP's violation is
        # then the light's distance from the line, in pixels.
        if np.linalg.norm(self.object_a - self.object_b) < 1e-9:
            d = self.object_a - s
            n = np.linalg.norm(d)
            if n < 1e-9:
                return np.zeros((0, 3))
            d = d / n
            normal = np.array([-d[1], d[0]])
            c = float(np.dot(normal, s))
            return np.array([[normal[0], normal[1], c], [-normal[0], -normal[1], -c]])
        rows = []
        for near, far in ((self.object_a, self.object_b), (self.object_b, self.object_a)):
            d = near - s
            n = np.linalg.norm(d)
            if n < 1e-9:
                continue
            d = d / n
            normal = np.array([-d[1], d[0]])           # perpendicular to the ray
            # orient so that the *other* ray's direction satisfies a.x <= b
            other = far - s
            if np.dot(normal, other) > 0:
                normal = -normal
            rows.append([normal[0], normal[1], float(np.dot(normal, s))])
        return np.array(rows) if rows else np.zeros((0, 3))

    def forward_constraint(self) -> np.ndarray:
        """Half-plane keeping the light on the object's side of the shadow
        point (the light is never behind the shadow, away from the object)."""
        d = 0.5 * (self.object_a + self.object_b) - self.shadow
        n = np.linalg.norm(d)
        if n < 1e-9:
            return np.zeros((0, 3))
        d = d / n
        return np.array([[-d[0], -d[1], float(-np.dot(d, self.shadow))]])


def _lp_min_violation(A: np.ndarray, b: np.ndarray, bound: float) -> tuple[float, np.ndarray | None]:
    """min t  s.t.  A L - b <= t,  |L| <= bound.  Returns (t, L)."""
    n = A.shape[0]
    if n == 0:
        return -np.inf, None
    # variables: Lx, Ly, t
    A_ub = np.hstack([A, -np.ones((n, 1))])
    res = linprog(c=[0, 0, 1], A_ub=A_ub, b_ub=b,
                  bounds=[(-bound, bound), (-bound, bound), (None, None)], method="highs")
    if not res.success:
        return np.inf, None
    return float(res.x[2]), res.x[:2]


def wedge_feasibility(pairs: list[ShadowPair], image_diag: float | None = None,
                      bound_factor: float = 50.0, use_forward: bool = True) -> dict:
    """Largest-violation LP over all wedges.

    `violation_px <= 0`: a single light explains every shadow, with margin
    `-violation_px` pixels.  `> 0`: no light does, and the value is how far
    (in pixels) the constraints are from admitting one.
    """
    rows = []
    for p in pairs:
        rows.append(p.half_planes())
        if use_forward:
            rows.append(p.forward_constraint())
    rows = [r for r in rows if len(r)]
    if not rows:
        return {"status": "no_constraints", "violation_px": np.nan, "n_pairs": len(pairs)}
    M = np.vstack(rows)
    A, b = M[:, :2], M[:, 2]
    diag = image_diag if image_diag else 1.0
    t, L = _lp_min_violation(A, b, bound_factor * diag)
    return {"status": "ok", "n_pairs": len(pairs), "n_constraints": int(len(b)),
            "violation_px": float(t),
            "light": None if L is None else L.tolist(),
            "feasible": bool(t <= 0)}


def light_vp_residual(pairs: list[ShadowPair]) -> dict:
    """Complementary to the LP: treat each exact shadow-object correspondence
    as a line and measure how well the lines meet at one point (the light's
    image), reusing the L2 concurrency machinery.  Only valid when the object
    point is known, i.e. `object_a == object_b`."""
    from .lines import Segments
    from .vp import estimate_vps

    exact = [p for p in pairs if np.allclose(p.object_a, p.object_b)]
    if len(exact) < 3:
        return {"status": "too_few_exact_pairs", "n": len(exact)}
    xy = np.array([[*p.shadow, *p.object_a] for p in exact])
    segs = Segments(xy)
    span = np.ptp(np.vstack([segs.p1, segs.p2]), axis=0)
    w, h = float(max(span[0], 1)), float(max(span[1], 1))
    r = estimate_vps(segs, int(w), int(h), n_vps=1, thresh_deg=90.0, n_iter=200)
    if len(r.vps) == 0:
        return {"status": "no_vp", "n": len(exact)}
    from .vp import angular_residuals
    res = angular_residuals(segs, r.vps[0])
    return {"status": "ok", "n": len(exact), "light_vp": r.vps[0].tolist(),
            "mean_deg": float(res.mean()), "max_deg": float(res.max()),
            "rms_deg": float(np.sqrt((res ** 2).mean()))}


# ----------------------------------------------------------------------------
# Shadow detection: gray-value transformation, thresholding, morphology
# ----------------------------------------------------------------------------

def shadow_index(image: np.ndarray) -> np.ndarray:
    """Gray-value transformation that separates cast shadows.

    Outdoor shadows are lit by blue skylight while sunlit surfaces get direct
    sun, so shadows are both *darker* and *bluer*.  In CIE Lab this is low L
    and low b (b is the yellow-blue axis), giving the normalised index
    (b - L) / (b + L + eps), which is largely invariant to surface albedo.
    Returned as float in [0, 1], higher = more shadow-like.
    """
    import cv2
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB).astype(np.float32)
    L, b = lab[..., 0] / 255.0, lab[..., 2] / 255.0
    idx = (b - L) / (b + L + 1e-3)
    return (idx - idx.min()) / max(float(np.ptp(idx)), 1e-6)


def shadow_mask(image: np.ndarray, min_area_frac: float = 0.002,
                close_frac: float = 0.01, open_frac: float = 0.004) -> dict:
    """Binary shadow mask by Otsu thresholding of `shadow_index` followed by
    morphological closing (bridge gaps) and opening (drop speckle).

    Structuring-element sizes scale with the image diagonal so the result is
    resolution independent.  Returns the mask, the labelled components kept
    after an area filter, and their statistics.
    """
    import cv2
    idx = (shadow_index(image) * 255).astype(np.uint8)
    _, raw = cv2.threshold(idx, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    diag = float(np.hypot(*image.shape[:2]))
    k_close = max(3, int(close_frac * diag) | 1)
    k_open = max(3, int(open_frac * diag) | 1)
    se_c = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k_close, k_close))
    se_o = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k_open, k_open))
    m = cv2.morphologyEx(raw, cv2.MORPH_CLOSE, se_c)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, se_o)
    n, lab, stats, cent = cv2.connectedComponentsWithStats(m, connectivity=8)
    area_min = min_area_frac * image.shape[0] * image.shape[1]
    keep = [i for i in range(1, n) if stats[i, cv2.CC_STAT_AREA] >= area_min]
    clean = np.isin(lab, keep).astype(np.uint8) * 255
    return {"mask": clean, "raw": raw, "index": idx, "labels": lab,
            "components": [{"id": int(i), "area": int(stats[i, cv2.CC_STAT_AREA]),
                            "centroid": cent[i].tolist(),
                            "bbox": stats[i, :4].tolist()} for i in keep],
            "shadow_frac": float((clean > 0).mean()),
            "k_close": k_close, "k_open": k_open}


# ----------------------------------------------------------------------------
# Automatic L7: shadow-axis concurrency and the horizon constraint
# ----------------------------------------------------------------------------

def shadow_axes(mask_result: dict, min_elongation: float = 2.0,
                min_extent_frac: float = 0.03, image_shape=None):
    """Major axis of every elongated shadow component, as line segments.

    For upright objects on a horizontal ground plane the shadow runs along the
    sun's azimuth, so all shadow axes are images of parallel 3D directions and
    must converge at one vanishing point.  The axis is taken as an *undirected*
    line through the component's centroid (PCA), which is why no
    object/attachment disambiguation is needed.
    """
    import numpy as np
    from .lines import Segments
    lab = mask_result["labels"]
    h, w = (image_shape[:2] if image_shape is not None else lab.shape[:2])
    diag = float(np.hypot(w, h))
    rows, info = [], []
    for comp in mask_result["components"]:
        ys, xs = np.nonzero(lab == comp["id"])
        if xs.size < 20:
            continue
        pts = np.stack([xs, ys], axis=1).astype(float)
        c = pts.mean(axis=0)
        _, sv, vt = np.linalg.svd(pts - c, full_matrices=False)
        d = vt[0]
        proj = (pts - c) @ d
        elong = float(sv[0] / max(sv[1], 1e-6))
        extent = float(np.ptp(proj))
        if elong < min_elongation or extent < min_extent_frac * diag:
            continue
        rows.append([*(c - 0.5 * extent * d), *(c + 0.5 * extent * d)])
        info.append({"id": comp["id"], "elongation": elong, "extent_px": extent,
                     "area": comp["area"]})
    return Segments(np.array(rows) if rows else np.zeros((0, 4))), info


def horizon_from_vps(vps: np.ndarray, width: int, height: int,
                     vert_tol_deg: float = 30.0):
    """Horizon line (homogeneous) through the two most-supported VPs that are
    not the vertical one.  The vertical VP is picked by direction from the
    image centre only, never by orthogonality."""
    import numpy as np
    pp = np.array([width / 2.0, height / 2.0])
    horiz = []
    for i, v in enumerate(vps):
        d = v[:2] - pp * v[2]
        if np.degrees(np.arctan2(abs(d[0]), abs(d[1]))) >= vert_tol_deg:
            horiz.append(i)
    if len(horiz) < 2:
        return None, horiz
    l = np.cross(vps[horiz[0]], vps[horiz[1]])
    n = np.linalg.norm(l[:2])
    return (l / n if n > 1e-12 else None), horiz[:2]


def shadow_consistency(image: np.ndarray, vps: np.ndarray | None = None,
                       min_axes: int = 3) -> dict:
    """L7 without object segmentation.

    1. shadow mask (threshold + morphology),
    2. major axis of each elongated shadow component,
    3. `axis_rms_deg`: how well those axes converge on one vanishing point -
       the image of the sun's azimuth (a single light implies one),
    4. `horizon_dist`: distance of that vanishing point from the horizon line
       implied by the scene's horizontal VPs, in image diagonals.  The sun's
       azimuth is a horizontal direction, so its VP must lie on the horizon.
    """
    import numpy as np
    from .vp import angular_residuals, estimate_vps
    h, w = image.shape[:2]
    mr = shadow_mask(image)
    axes, info = shadow_axes(mr, image_shape=image.shape)
    out = {"shadow_frac": mr["shadow_frac"], "n_components": len(mr["components"]),
           "n_axes": len(axes), "axis_rms_deg": np.nan, "axis_max_deg": np.nan,
           "horizon_dist": np.nan, "status": "ok"}
    if len(axes) < min_axes:
        out["status"] = "too_few_shadow_axes"
        return out
    r = estimate_vps(axes, w, h, n_vps=1, thresh_deg=90.0, n_iter=300, min_support=2)
    if len(r.vps) == 0:
        out["status"] = "no_shadow_vp"
        return out
    res = angular_residuals(axes, r.vps[0])
    out["axis_rms_deg"] = float(np.sqrt((res ** 2).mean()))
    out["axis_max_deg"] = float(res.max())
    out["shadow_vp"] = r.vps[0].tolist()
    if vps is not None and len(vps) >= 2:
        hor, used = horizon_from_vps(np.asarray(vps, float), w, h)
        if hor is not None:
            v = r.vps[0]
            denom = abs(v[2]) * float(np.hypot(w, h))
            if denom > 1e-9:
                out["horizon_dist"] = float(abs(hor @ v) / denom)
            else:
                out["horizon_dist"] = 0.0     # VP at infinity lies on any line direction-wise
            out["horizon_vps"] = used
    return out
