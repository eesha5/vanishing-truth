"""A folder of images, read in sorted filename order so that image i is
always the same file (generated images are numbered by prompt)."""

from pathlib import Path

import cv2

IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg")


def image_files(folder, limit: int | None = None) -> list[Path]:
    files = sorted(p for p in Path(folder).iterdir() if p.suffix.lower() in IMAGE_SUFFIXES)
    return files[:limit] if limit else files


def load_folder(folder, limit: int | None = None) -> list[tuple[str, "cv2.typing.MatLike"]]:
    """[(file name, BGR image), ...] for every image in `folder`."""
    return [(p.name, cv2.imread(str(p))) for p in image_files(folder, limit)]
