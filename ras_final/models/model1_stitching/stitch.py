"""Panorama stitching for overlapping drone frames."""
from __future__ import annotations

from typing import Iterable
import logging

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class Stitcher:
    """Wrap OpenCV's Stitcher with input validation and a callable API."""

    def __init__(self, mode: int = cv2.Stitcher_PANORAMA, resize_width: int | None = None) -> None:
        if resize_width is not None and resize_width <= 0:
            raise ValueError("resize_width must be positive or None")
        self.resize_width = resize_width
        self._stitcher = cv2.Stitcher_create(mode)

    def __call__(self, frames: Iterable[np.ndarray]) -> np.ndarray:
        images = [self._resize(frame) for frame in frames if frame is not None and frame.size]
        if len(images) < 2:
            raise ValueError("stitching requires at least two non-empty frames")
        try:
            status, panorama = self._stitcher.stitch(images)
        except (cv2.error, RuntimeError) as exc:
            logger.warning("OpenCV stitching raised %s; using latest frame", exc)
            return images[-1]
        if status != cv2.Stitcher_OK or panorama is None or panorama.size == 0:
            logger.warning("OpenCV stitching failed with status %s; using latest frame", status)
            return images[-1]
        return panorama

    def stitch(self, frames: Iterable[np.ndarray]) -> np.ndarray:
        return self(frames)

    def _resize(self, frame: np.ndarray) -> np.ndarray:
        if self.resize_width is None or frame.shape[1] <= self.resize_width:
            return frame
        scale = self.resize_width / frame.shape[1]
        return cv2.resize(frame, (self.resize_width, max(1, round(frame.shape[0] * scale))), interpolation=cv2.INTER_AREA)


def stitch_frames(frames: Iterable[np.ndarray]) -> np.ndarray:
    return Stitcher()(frames)
