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


# ----------------------------------------------------------------------------
# Shadow scenes for L7
# ----------------------------------------------------------------------------

@dataclass
class ShadowScene:
    pairs: list          # list of (shadow_point, object_point) in pixels
    K: np.ndarray
    R: np.ndarray
    light_dir: np.ndarray        # unit 3D direction *towards* the light (world)
    light_image: np.ndarray      # homogeneous image of the light direction
    width: int
    height: int


def make_shadow_scene(n_objects: int = 8, width: int = 1024, height: int = 768,
                      f: float | None = None, sun_elev_deg: float = 40.0,
                      sun_azim_deg: float = 30.0, seed: int = 0,
                      noise_px: float = 0.5, max_tries: int = 4000) -> ShadowScene:
    """Upright poles on the ground plane lit by a distant sun.

    World axes follow the image convention (x right, **y down**, z forward),
    so the ground plane sits at y = +camera height and "up" is -y.  Base
    points are sampled in image space and back-projected onto the ground
    plane, which guarantees every object is in frame; heights are resampled
    until the pole top and its shadow tip are in frame as well.  The pole top
    and its shadow tip are joined by a line through the image of the sun
    direction, so a consistent light exists by construction.
    """
    rng = np.random.default_rng(seed)
    if f is None:
        f = rng.uniform(0.8, 1.2) * max(width, height)
    K = np.array([[f, 0, width / 2], [0, f, height / 2], [0, 0, 1.0]])
    Kinv = np.linalg.inv(K)
    pitch = np.radians(rng.uniform(-12, 12))       # small camera pitch
    R = np.array([[1, 0, 0],
                  [0, np.cos(pitch), -np.sin(pitch)],
                  [0, np.sin(pitch), np.cos(pitch)]])
    cam_h = 1.6
    ground_y = cam_h                               # y grows downwards
    el, az = np.radians(sun_elev_deg), np.radians(sun_azim_deg)
    # unit vector pointing *towards* the sun; up is -y
    light = np.array([np.cos(el) * np.sin(az), -np.sin(el), np.cos(el) * np.cos(az)])
    light /= np.linalg.norm(light)

    def project(P_world):
        P = P_world @ R.T                          # world -> camera
        if np.any(P[:, 2] < 0.5):
            return None
        p = P @ K.T
        return p[:, :2] / p[:, 2:3]

    def backproject_ground(px):
        ray = R.T @ (Kinv @ np.array([px[0], px[1], 1.0]))   # camera -> world
        if ray[1] <= 1e-6:                         # at or above the horizon
            return None
        P = (ground_y / ray[1]) * ray
        return P if P[2] > 1.0 else None

    pairs = []
    for _ in range(max_tries):
        if len(pairs) >= n_objects:
            break
        px = np.array([rng.uniform(0.08 * width, 0.92 * width),
                       rng.uniform(0.55 * height, 0.97 * height)])
        base = backproject_ground(px)
        if base is None:
            continue
        hgt = rng.uniform(0.4, 2.5)
        top = base + np.array([0.0, -hgt, 0.0])              # up is -y
        tip = top + (hgt / np.sin(el)) * (-light)            # away from the sun
        p = project(np.stack([top, tip]))
        if p is None:
            continue
        if (p < 0).any() or p[:, 0].max() >= width or p[:, 1].max() >= height:
            continue
        if np.linalg.norm(p[1] - p[0]) < 0.03 * np.hypot(width, height):
            continue
        p = p + rng.normal(0, noise_px, p.shape)
        pairs.append((p[1], p[0]))                 # (shadow tip, object top)
    if len(pairs) < 3:
        raise RuntimeError(f"could not build a shadow scene for seed {seed}")
    light_image = K @ R @ light                    # image of the sun direction
    return ShadowScene(pairs, K, R, light, light_image, width, height)


def perturb_shadow(pairs: list, index: int, angle_deg: float) -> list:
    """Rotate one shadow point about its object point: the classic
    'shadow points the wrong way' manipulation."""
    out = [(np.array(s, float), np.array(o, float)) for s, o in pairs]
    s, o = out[index]
    a = np.radians(angle_deg)
    c, si = np.cos(a), np.sin(a)
    d = s - o
    out[index] = (o + np.array([c * d[0] - si * d[1], si * d[0] + c * d[1]]), o)
    return out
