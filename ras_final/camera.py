"""Camera abstraction for the Raspberry Pi SAR runtime.

Uses Picamera2 when available; otherwise falls back to OpenCV video capture or a static input.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable

import cv2
import numpy as np

try:
    from picamera2 import Picamera2  # type: ignore
except Exception:  # pragma: no cover - optional dependency on Pi only.
    Picamera2 = None  # type: ignore


logger = logging.getLogger(__name__)


class CameraSource:
    """Read frames from a Raspberry Pi camera or a local fallback source."""

    def __init__(self, source: str | int | None = None, prefer_picamera: bool = True) -> None:
        self.source = source
        self.prefer_picamera = prefer_picamera
        self._capture: cv2.VideoCapture | None = None
        self._picam: Picamera2 | None = None

    def open(self) -> None:
        if self._capture is not None or self._picam is not None:
            return

        if self.prefer_picamera and Picamera2 is not None and self.source in (None, 0):
            try:
                self._picam = Picamera2()
                config = self._picam.create_preview_configuration(main={"size": (640, 480)})
                self._picam.configure(config)
                self._picam.start()
                logger.info("Picamera2 initialized")
                return
            except Exception as exc:  # pragma: no cover - platform dependent.
                logger.warning("Picamera2 unavailable, falling back to OpenCV: %s", exc)

        if isinstance(self.source, (str, Path)):
            path = Path(self.source)
            if path.exists() and path.is_file():
                self._capture = cv2.VideoCapture(str(path))
                logger.info("Using static video/image source: %s", path)
                return

        camera_index = 0 if self.source is None else self.source
        self._capture = cv2.VideoCapture(int(camera_index) if isinstance(camera_index, int) else str(camera_index))
        if not self._capture.isOpened():
            raise RuntimeError(f"Unable to open camera source: {self.source!r}")
        logger.info("OpenCV camera initialized from source %r", self.source)

    def read(self) -> np.ndarray | None:
        self.open()
        if self._picam is not None:
            frame = self._picam.capture_array()
            if frame is None:
                return None
            return np.asarray(frame)

        if self._capture is None:
            return None

        ok, frame = self._capture.read()
        if not ok or frame is None or frame.size == 0:
            return None
        return frame

    def read_many(self, count: int = 2) -> list[np.ndarray]:
        frames: list[np.ndarray] = []
        for _ in range(count):
            frame = self.read()
            if frame is None:
                break
            frames.append(frame)
        return frames

    def close(self) -> None:
        if self._capture is not None:
            self._capture.release()
            self._capture = None
        if self._picam is not None:
            self._picam.stop()
            self._picam = None


if __name__ == "__main__":
    source = CameraSource(source=None, prefer_picamera=True)
    frame = source.read()
    print(type(frame).__name__ if frame is not None else "no-frame")
    source.close()
