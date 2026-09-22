"""Synthetic Manhattan scenes with a known camera, plus controlled violations.

This is the cheap, exact precursor of the Blender injection suite (§3.4 of the
plan): we know the camera, the VPs and the axis label of every segment, so
we can (a) check the estimators recover the truth on clean data and
(b) inject one specific violation and measure how each residual responds.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.spatial.transform import Rotation

from .geometry import unit
from .lines import Segments


@dataclass
class SynthScene:
    segs: Segments
    labels: np.ndarray        # axis id (0=x, 1=y, 2=z) per segment
    K: np.ndarray
    R: np.ndarray
    width: int
    height: int

    @property
    def vps(self) -> np.ndarray:
        """Ground-truth homogeneous VPs (unit norm), one per world axis."""
        return unit((self.K @ self.R).T)  # column k of K R

    @property
    def f(self) -> float:
        return float(self.K[0, 0])


def make_scene(n_segments: int = 150, width: int = 1024, height: int = 768,
               f: float | None = None, max_tilt_deg: float = 25.0,
               noise_px: float = 0.5, seed: int = 0) -> SynthScene:
    """Random pinhole camera at the origin inside a box of axis-aligned
    3D segments.  Only segments fully inside the image are kept."""
    rng = np.random.default_rng(seed)
    if f is None:
        f = rng.uniform(0.6, 1.4) * max(width, height)
    K = np.array([[f, 0, width / 2], [0, f, height / 2], [0, 0, 1.0]])
    # camera looks roughly down +z of the world with a random moderate rotation
    rot = Rotation.from_euler("xyz", rng.uniform(-max_tilt_deg, max_tilt_deg, 3), degrees=True)
    R = rot.as_matrix()

    xy, labels = [], []
    tries = 0
    while len(xy) < n_segments and tries < 50 * n_segments:
        tries += 1
        axis = rng.integers(0, 3)
        start = np.array([rng.uniform(-6, 6), rng.uniform(-6, 6), rng.uniform(3, 14)])
        length = rng.uniform(0.5, 4.0)
        end = start.copy()
        end[axis] += length * rng.choice([-1, 1])
        P = np.stack([start, end]) @ R.T          # world -> camera
        if (P[:, 2] < 0.5).any():
            continue
        p = (P @ K.T)
        p = p[:, :2] / p[:, 2:3]
        if (p < 0).any() or p[:, 0].max() >= width or p[:, 1].max() >= height:
            continue
        if np.linalg.norm(p[1] - p[0]) < 0.02 * np.hypot(width, height):
            continue
        p = p + rng.normal(0, noise_px, p.shape)
        xy.append(p.ravel())
        labels.append(axis)
    return SynthScene(Segments(np.array(xy)), np.array(labels), K, R, width, height)


# ----------------------------------------------------------------------------
# Violation injection.  Each returns a new Segments with the same labels.
# ----------------------------------------------------------------------------

def _reaim(segs: Segments, mask: np.ndarray, targets: np.ndarray) -> Segments:
    """Rotate masked segments about their midpoints so they point at the
    (per-segment) homogeneous target points `targets` (M,3)."""
    xy = segs.xy.copy()
    mid = segs.midpoints[mask]
    L = segs.lengths[mask]
    t = targets
    finite = np.abs(t[:, 2]) > 1e-9
    d = np.empty_like(mid)
    d[finite] = t[finite, :2] / t[finite, 2:3] - mid[finite]
    d[~finite] = t[~finite, :2]
    d = unit(d)
    # keep original orientation sign
    d *= np.sign(np.sum(d * segs.directions[mask], axis=1, keepdims=True) + 1e-12)
    xy[mask, :2] = mid - 0.5 * L[:, None] * d
    xy[mask, 2:] = mid + 0.5 * L[:, None] * d
    return Segments(xy)


def jitter_directions(segs: Segments, labels: np.ndarray, axis: int,
                      sigma_deg: float, seed: int = 0) -> Segments:
    """L2 violation: rotate every segment of one axis by N(0, sigma) degrees
    about its midpoint.  Lines no longer meet at one point."""
    rng = np.random.default_rng(seed)
    xy = segs.xy.copy()
    m = labels == axis
    ang = np.radians(rng.normal(0, sigma_deg, m.sum()))
    mid = segs.midpoints[m]
    L = segs.lengths[m]
    d = segs.directions[m]
    c, s = np.cos(ang), np.sin(ang)
    d2 = np.stack([c * d[:, 0] - s * d[:, 1], s * d[:, 0] + c * d[:, 1]], axis=1)
    xy[m, :2] = mid - 0.5 * L[:, None] * d2
    xy[m, 2:] = mid + 0.5 * L[:, None] * d2
    return Segments(xy)


def shift_vp(scene: SynthScene, axis: int, shift_px: np.ndarray) -> Segments:
    """L3 violation: re-aim one axis' segments at a VP displaced by `shift_px`.
    Concurrency (L2) stays perfect; the three VPs are no longer orthogonal."""
    vp = scene.vps[axis]
    if abs(vp[2]) < 1e-9:
        raise ValueError("cannot shift a VP at infinity in pixels")
    target = np.array([vp[0] / vp[2] + shift_px[0], vp[1] / vp[2] + shift_px[1], 1.0])
    m = scene.labels == axis
    return _reaim(scene.segs, m, np.tile(target, (m.sum(), 1)))


def drift_vp(scene: SynthScene, axis: int, drift_px: np.ndarray) -> Segments:
    """Locality violation (the paper's central hypothesis): the effective VP
    of one axis moves linearly with the segment's horizontal image position,
    from vp - drift/2 on the left edge to vp + drift/2 on the right edge.
    Nearby segments agree almost perfectly; distant ones do not."""
    vp = scene.vps[axis]
    if abs(vp[2]) < 1e-9:
        raise ValueError("cannot drift a VP at infinity in pixels")
    m = scene.labels == axis
    u = scene.segs.midpoints[m, 0] / scene.width - 0.5
    base = vp[:2] / vp[2]
    targets = np.concatenate([base + u[:, None] * drift_px[None, :], np.ones((m.sum(), 1))], axis=1)
    return _reaim(scene.segs, m, targets)


def two_cameras(scene: SynthScene, f_ratio: float = 1.0, rot_deg: float = 0.0,
                axis_frac: float = 0.5) -> Segments:
    """Regional violation: segments whose midpoint lies right of `axis_frac`
    of the width are re-aimed at the VPs of a *different* camera (focal
    scaled by f_ratio, rotated by rot_deg about a fixed axis).  Every line
    family still converges (L2 fine), each half is a valid camera, but no
    single camera explains the whole image."""
    K2 = scene.K.copy()
    K2[0, 0] *= f_ratio
    K2[1, 1] *= f_ratio
    R2 = Rotation.from_euler("y", rot_deg, degrees=True).as_matrix() @ scene.R
    vps2 = (K2 @ R2).T
    right = scene.segs.midpoints[:, 0] > axis_frac * scene.width
    xy = scene.segs.xy.copy()
    out = Segments(xy)
    for axis in range(3):
        m = right & (scene.labels == axis)
        if not m.any():
            continue
        out = _reaim(out, m, np.tile(vps2[axis], (m.sum(), 1)))
    return out
