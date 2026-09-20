"""Estimator validation on synthetic scenes with known cameras."""

import numpy as np
import pytest

from projgeo.camera import vp_rays
from projgeo.pipeline import analyze_segments
from projgeo.synth import drift_vp, jitter_directions, make_scene, shift_vp

SEEDS = [0, 1, 2, 3, 4]


def _match_angles(sc, vps):
    pp = [sc.width / 2, sc.height / 2]
    gt = vp_rays(sc.vps, sc.f, pp)
    est = vp_rays(vps, sc.f, pp)
    ang = np.degrees(np.arccos(np.clip(np.abs(est @ gt.T), 0, 1)))
    return ang.min(axis=1)


@pytest.mark.parametrize("seed", SEEDS)
def test_clean_scene_recovers_camera(seed):
    sc = make_scene(seed=seed)
    rep = analyze_segments(sc.segs, sc.width, sc.height)
    assert rep["L3"]["n_vps"] == 3
    assert (_match_angles(sc, rep["_vp_result"].vps) < 0.5).all()
    assert abs(rep["L3"]["f_fit"] - sc.f) / sc.f < 0.03
    assert rep["L3"]["ortho_err_max_deg"] < 0.5
    assert rep["L3"]["n_negative_f2"] == 0
    assert rep["L2"]["all"]["unexplained_frac"] < 0.02


def _sweep(fn, levels):
    vals = []
    for lv in levels:
        v = []
        for seed in SEEDS[:3]:
            sc = make_scene(seed=seed)
            v.append(fn(sc, lv))
        vals.append(np.mean(v))
    return np.array(vals)


def test_l2_residual_grows_with_jitter():
    def f(sc, sigma):
        segs = jitter_directions(sc.segs, sc.labels, 0, sigma, seed=1)
        return analyze_segments(segs, sc.width, sc.height)["L2"]["all"]["capped_mean_deg"]
    v = _sweep(f, [0, 1, 2, 4, 8])
    assert (np.diff(v) > 0).all(), v


def test_l3_residual_grows_with_vp_shift_and_l2_does_not():
    def f(sc, shift):
        rep = analyze_segments(shift_vp(sc, 2, np.array([shift, 0.0])), sc.width, sc.height)
        return rep["L3"]["ortho_err_max_deg"], rep["L2"]["all"]["capped_mean_deg"]
    levels = [0, 100, 200, 400]
    out = np.array([[f(make_scene(seed=s), lv) for s in SEEDS[:3]] for lv in levels]).mean(axis=1)
    ortho, l2 = out[:, 0], out[:, 1]
    assert (np.diff(ortho) > 0).all(), ortho
    assert ortho[-1] > 5.0
    assert l2.max() - l2.min() < 0.1, l2   # concurrency untouched by a pure VP shift


def test_locality_drift_raises_l2():
    def f(sc, drift):
        segs = drift_vp(sc, 2, np.array([drift, 0.0]))
        return analyze_segments(segs, sc.width, sc.height)["L2"]["all"]["capped_mean_deg"]
    v = _sweep(f, [0, 100, 200, 400])
    assert (np.diff(v) > 0).all(), v
