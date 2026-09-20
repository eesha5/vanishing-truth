import numpy as np

from projgeo.camera import l3_report, orthocenter, pairwise_focal
from projgeo.geometry import line_through, to_inhomogeneous
from projgeo.lines import Segments
from projgeo.vp import angular_residuals


def test_line_through_and_residual_at_infinity():
    segs = Segments([[0, 0, 10, 0], [0, 5, 10, 5.5]])
    r = angular_residuals(segs, np.array([1.0, 0.0, 0.0]))   # horizontal VP at infinity
    assert np.isclose(r[0], 0.0)
    assert np.isclose(r[1], np.degrees(np.arctan2(0.5, 10)))


def test_orthocenter_gives_consistent_focal():
    # Build VPs from a known camera; orthocentre must be the principal point
    f, w, h = 900.0, 800, 600
    K = np.array([[f, 0, w / 2], [0, f, h / 2], [0, 0, 1]])
    from scipy.spatial.transform import Rotation
    R = Rotation.from_euler("xyz", [20, 30, 10], degrees=True).as_matrix()
    vps = (K @ R).T
    oc = orthocenter(vps)
    assert np.allclose(oc, [w / 2, h / 2], atol=1e-6)
    rep = l3_report(vps, w, h)
    assert abs(rep["f_fit"] - f) / f < 1e-3
    assert rep["ortho_err_max_deg"] < 1e-3
    for d in pairwise_focal(vps, np.array([w / 2, h / 2])):
        assert abs(d["f"] - f) / f < 1e-6


def test_l3_handles_vp_at_infinity():
    f, w, h = 900.0, 800, 600
    K = np.array([[f, 0, w / 2], [0, f, h / 2], [0, 0, 1]])
    from scipy.spatial.transform import Rotation
    R = Rotation.from_euler("y", 30, degrees=True).as_matrix()  # level camera: vertical VP at infinity
    vps = (K @ R).T
    assert to_inhomogeneous(vps[1]) is None
    rep = l3_report(vps, w, h)
    assert rep["status"] == "ok"
    assert rep["orthocenter"] is None
    assert rep["ortho_err_max_deg"] < 1e-3
    assert abs(rep["f_fit"] - f) / f < 1e-3
