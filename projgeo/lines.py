"""Line-segment detection and the Segments container."""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from .geometry import hom, line_through, unit


@dataclass
class Segments:
    """N line segments as an (N,4) array of x1, y1, x2, y2 in pixels."""

    xy: np.ndarray

    def __post_init__(self):
        self.xy = np.asarray(self.xy, dtype=float).reshape(-1, 4)

    def __len__(self) -> int:
        return self.xy.shape[0]

    def __getitem__(self, idx) -> "Segments":
        return Segments(self.xy[idx])

    @property
    def p1(self) -> np.ndarray:
        return self.xy[:, :2]

    @property
    def p2(self) -> np.ndarray:
        return self.xy[:, 2:]

    @property
    def midpoints(self) -> np.ndarray:
        return 0.5 * (self.p1 + self.p2)

    @property
    def lengths(self) -> np.ndarray:
        return np.linalg.norm(self.p2 - self.p1, axis=1)

    @property
    def directions(self) -> np.ndarray:
        return unit(self.p2 - self.p1)

    @property
    def lines(self) -> np.ndarray:
        """(N,3) homogeneous lines with unit (a, b)."""
        return line_through(hom(self.p1), hom(self.p2))

    def transformed(self, T: np.ndarray) -> "Segments":
        """Apply a 3x3 homography to both endpoints."""
        P1 = hom(self.p1) @ T.T
        P2 = hom(self.p2) @ T.T
        P1 = P1[:, :2] / P1[:, 2:3]
        P2 = P2[:, :2] / P2[:, 2:3]
        return Segments(np.concatenate([P1, P2], axis=1))

    def filter_length(self, min_length: float) -> "Segments":
        return self[self.lengths >= min_length]


def detect_lsd(image: np.ndarray, min_length: float | None = None,
               scale: float = 0.8) -> Segments:
    """Detect segments with OpenCV's LSD (von Gioi et al.).

    `min_length` defaults to 2% of the image diagonal, which removes the
    texture clutter that otherwise dominates VP voting.
    """
    if image.ndim == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    lsd = cv2.createLineSegmentDetector(cv2.LSD_REFINE_STD, scale=scale)
    out = lsd.detect(gray)[0]
    if out is None or len(out) == 0:
        return Segments(np.zeros((0, 4)))
    segs = Segments(out.reshape(-1, 4))
    if min_length is None:
        min_length = 0.02 * float(np.hypot(*gray.shape))
    return segs.filter_length(min_length)
