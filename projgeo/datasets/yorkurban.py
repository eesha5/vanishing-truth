"""York Urban Line Segment Database (Denis, Elder & Estrada, ECCV 2008).

102 calibrated 640x480 images with hand-labelled line segments and their
Manhattan VP assignment.  Ground-truth VP directions are stored as the
*columns* of `vp` in a camera frame with y pointing up; the image VP is
K . diag(1,-1,1) . vp[:, k]  (verified: labelled lines sit ~0.5 deg from it).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
import scipy.io as sio

from ..geometry import unit
from ..lines import Segments


@dataclass
class YorkUrbanImage:
    name: str
    image: np.ndarray            # BGR
    K: np.ndarray                # (3,3) true intrinsics
    vps: np.ndarray              # (3,3) GT homogeneous image VPs, unit norm (rows)
    vp_dirs: np.ndarray          # (3,3) GT unit 3D directions (rows), image-frame convention
    gt_segments: Segments        # hand-labelled inlier segments
    gt_labels: np.ndarray        # VP index 0..2 per GT segment

    @property
    def width(self) -> int:
        return self.image.shape[1]

    @property
    def height(self) -> int:
        return self.image.shape[0]

    @property
    def f(self) -> float:
        return float(self.K[0, 0])


class YorkUrban:
    def __init__(self, root: str | Path = "data/real/YorkUrbanDB"):
        self.root = Path(root)
        cam = sio.loadmat(self.root / "cameraParameters.mat")
        f = float(cam["focal"].item() / cam["pixelSize"].item())
        pp = cam["pp"].ravel()
        self.K = np.array([[f, 0, pp[0]], [0, f, pp[1]], [0, 0, 1.0]])
        names = sio.loadmat(self.root / "Manhattan_Image_DB_Names.mat")["Manhattan_Image_DB_Names"]
        self.names = [str(n[0][0]).strip("\\/") for n in names]
        split = sio.loadmat(self.root / "ECCV_TrainingAndTestImageNumbers.mat")
        self.train_idx = split["trainingSetIndex"].ravel() - 1
        self.test_idx = split["testSetIndex"].ravel() - 1

    def __len__(self) -> int:
        return len(self.names)

    def __getitem__(self, i: int) -> YorkUrbanImage:
        name = self.names[i]
        d = self.root / name
        img = cv2.imread(str(d / f"{name}.jpg"), cv2.IMREAD_COLOR)
        g = sio.loadmat(d / f"{name}GroundTruthVP_CamParams.mat")
        m = sio.loadmat(d / f"{name}LinesAndVP.mat")
        dirs = (np.diag([1.0, -1.0, 1.0]) @ g["vp"]).T            # rows = directions
        vps = unit(dirs @ self.K.T)                               # K d  (row form)
        lines = m["lines"].reshape(-1, 4)
        labels = m["vp_association"].ravel().astype(int) - 1
        return YorkUrbanImage(name, img, self.K, vps, unit(dirs), Segments(lines), labels)

    def __iter__(self):
        for i in range(len(self)):
            yield self[i]
