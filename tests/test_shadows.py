"""L7 validation on synthetic scenes with a known single light."""

import numpy as np

from projgeo.lines import Segments
from projgeo.shadows import ShadowPair, light_vp_residual, wedge_feasibility
from projgeo.synth import make_shadow_scene, perturb_shadow
from projgeo.vp import angular_residuals, estimate_vps

DIAG = float(np.hypot(1024, 768))


def _pairs(pl, half_width):
    """Shadow pairs whose object region is a segment of half-width `half_width`
    perpendicular to the shadow direction (annotation uncertainty)."""
    out = []
    for s, o in pl:
        d = np.asarray(o, float) - np.asarray(s, float)
        d = d / max(np.linalg.norm(d), 1e-9)
        perp = np.array([-d[1], d[0]])
        out.append(ShadowPair(s, o - half_width * perp, o + half_width * perp))
    return out


def test_consistent_light_is_feasible():
    sc = make_shadow_scene(seed=0, n_objects=10)
    r = wedge_feasibility(_pairs(sc.pairs, 5.0), image_diag=DIAG)
    assert r["feasible"], r
    assert r["n_pairs"] == len(sc.pairs)


def test_violation_grows_with_perturbation():
    sc = make_shadow_scene(seed=0, n_objects=10)
    vals = []
    for ang in (0, 5, 10, 20):
        pl = perturb_shadow(sc.pairs, 0, ang) if ang else sc.pairs
        vals.append(wedge_feasibility(_pairs(pl, 5.0), image_diag=DIAG)["violation_px"])
    assert (np.diff(vals) > 0).all(), vals
    assert vals[0] < 0 < vals[-1]


def test_wider_uncertainty_is_more_permissive():
    """A wedge must never report a violation smaller than a narrower one:
    more annotation uncertainty can only make the test more forgiving."""
    sc = make_shadow_scene(seed=1, n_objects=10)
    pl = perturb_shadow(sc.pairs, 0, 10)
    v = [wedge_feasibility(_pairs(pl, hw), image_diag=DIAG)["violation_px"] for hw in (2.0, 5.0, 15.0)]
    assert v[0] > v[1] > v[2], v


def test_shadow_axis_concurrency_grows_with_perturbation():
    sc = make_shadow_scene(seed=0, n_objects=10, noise_px=0.2)
    vals = []
    for ang in (0, 5, 10, 20):
        pl = perturb_shadow(sc.pairs, 0, ang) if ang else sc.pairs
        segs = Segments(np.array([[*s, *o] for s, o in pl]))
        r = estimate_vps(segs, sc.width, sc.height, n_vps=1, thresh_deg=90.0,
                         n_iter=300, min_support=2)
        res = angular_residuals(segs, r.vps[0])
        vals.append(float(np.sqrt((res ** 2).mean())))
    assert (np.diff(vals) > 0).all(), vals
    assert vals[-1] > 3 * vals[0], vals


def test_light_vp_residual_recovers_sun_direction():
    sc = make_shadow_scene(seed=2, n_objects=10)
    v = light_vp_residual([ShadowPair(s, o, o) for s, o in sc.pairs])
    assert v["status"] == "ok"
    assert v["rms_deg"] < 1.0
    est = np.array(v["light_vp"])
    gt = sc.light_image / np.linalg.norm(sc.light_image)
    # same point up to sign
    assert abs(abs(est @ gt) - 1) < 1e-2, (est, gt)


def test_shadow_mask_finds_a_dark_blob():
    import cv2
    img = np.full((240, 320, 3), 200, np.uint8)
    cv2.rectangle(img, (40, 120), (200, 150), (120, 90, 60), -1)  # dark, bluish
    from projgeo.shadows import shadow_axes, shadow_mask
    mr = shadow_mask(img, min_area_frac=0.001)
    assert mr["shadow_frac"] > 0.01
    axes, info = shadow_axes(mr, image_shape=img.shape)
    assert len(axes) >= 1
    d = axes.directions[0]
    assert abs(d[1]) < 0.3      # the blob is horizontal
