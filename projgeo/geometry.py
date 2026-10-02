"""Homogeneous-coordinate helpers.

Conventions: image coordinates are pixels, origin top-left, x right, y down.
Points and lines are 3-vectors; a line (a, b, c) satisfies a x + b y + c = 0.
"""

import numpy as np


def hom(p: np.ndarray) -> np.ndarray:
    """(N,2) -> (N,3) homogeneous points."""
    p = np.asarray(p, dtype=float)
    return np.concatenate([p, np.ones((*p.shape[:-1], 1))], axis=-1)


def unit(v: np.ndarray, axis: int = -1, eps: float = 1e-12) -> np.ndarray:
    v = np.asarray(v, dtype=float)
    n = np.linalg.norm(v, axis=axis, keepdims=True)
    return v / np.maximum(n, eps)


def line_through(p1: np.ndarray, p2: np.ndarray) -> np.ndarray:
    """Line through two homogeneous points, normalized so (a, b) is unit."""
    l = np.cross(p1, p2)
    n = np.linalg.norm(l[..., :2], axis=-1, keepdims=True)
    return l / np.maximum(n, 1e-12)


def line_direction(l: np.ndarray) -> np.ndarray:
    """Unit direction vector of image line(s) (a, b, c) -> (-b, a)."""
    d = np.stack([-l[..., 1], l[..., 0]], axis=-1)
    return unit(d)


def normalizing_transform(width: int, height: int) -> np.ndarray:
    """T mapping pixels to centered coordinates scaled by half the max side.

    Working in these coordinates keeps RANSAC/least squares well conditioned
    and makes points at infinity behave.
    """
    s = 2.0 / max(width, height)
    return np.array([[s, 0, -s * width / 2.0],
                     [0, s, -s * height / 2.0],
                     [0, 0, 1.0]])


def to_inhomogeneous(v: np.ndarray, eps: float = 1e-9):
    """Return (x, y) or None if the point is (numerically) at infinity."""
    v = np.asarray(v, dtype=float)
    scale = np.linalg.norm(v[:2])
    if abs(v[2]) < eps * max(scale, 1.0):
        return None
    return v[:2] / v[2]
