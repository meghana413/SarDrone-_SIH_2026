"""Portable YOLO inference for images, videos, USB cameras, and Pi cameras."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Mapping

import cv2
import numpy as np

SUPPORTED_BACKENDS = {"pytorch", "onnx", "ncnn"}


def _resolve_device(_: str | int = "cpu") -> str:
    return "cpu"


@dataclass(frozen=True)
class Detection:
    x1: float
    y1: float
    x2: float
    y2: float
    class_id: int
    class_name: str
    confidence: float

    @property
    def bbox(self) -> list[float]:
        return [self.x1, self.y1, self.x2, self.y2]

    def as_dict(self) -> dict[str, Any]:
        return {"class_id": self.class_id, "class_name": self.class_name,
                "confidence": self.confidence, "bbox": self.bbox}


class Detector:
    def __init__(self, weights: str | Path, confidence: float = 0.35, iou: float = 0.5,
                 device: str | int = "cpu", backend: str = "pytorch", imgsz: int = 640) -> None:
        if backend not in SUPPORTED_BACKENDS:
            raise ValueError(f"unsupported backend {backend!r}; choose from {sorted(SUPPORTED_BACKENDS)}")
        if not 0.0 <= confidence <= 1.0 or not 0.0 <= iou <= 1.0:
            raise ValueError("confidence and iou must be between 0 and 1")
        self.weights, self.confidence, self.iou = str(weights), confidence, iou
        self.device, self.backend, self.imgsz, self._model = _resolve_device(device), backend, imgsz, None

    @property
    def model(self) -> Any:
        if self._model is None:
            path = Path(self.weights)
            if not path.exists():
                raise FileNotFoundError(f"model file/directory not found: {path}")
            from ultralytics import YOLO
            self._model = YOLO(self.weights)
        return self._model

    def predict(self, frame: np.ndarray) -> list[Detection]:
        if frame is None or frame.size == 0:
            raise ValueError("frame must be a non-empty image")
        results = self.model.predict(source=frame, imgsz=self.imgsz, conf=self.confidence,
                                     iou=self.iou, device=self.device, verbose=False)
        if not results or results[0].boxes is None:
            return []
        boxes, detections = results[0].boxes, []
        for coordinates, score, class_id in zip(boxes.xyxy.cpu().tolist(), boxes.conf.cpu().tolist(), boxes.cls.cpu().tolist()):
            if int(class_id) == 0:
                detections.append(Detection(*map(float, coordinates), 0, "victim", float(score)))
        return detections


def _source_value(source: str | int) -> str | int:
    return int(source) if isinstance(source, str) and source.isdigit() else source


def infer_source(detector: Detector, source: str | int) -> Iterator[tuple[np.ndarray, list[Detection]]]:
    source = _source_value(source)
    image_suffixes = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    if isinstance(source, str) and Path(source).is_file() and Path(source).suffix.lower() in image_suffixes:
        frame = cv2.imread(source)
        if frame is None:
            raise OSError(f"unable to read image {source!r}")
        yield frame, detector.predict(frame)
        return
    capture = cv2.VideoCapture(source)
    if not capture.isOpened():
        capture.release()
        raise OSError(f"unable to open video/camera source {source!r}")
    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            yield frame, detector.predict(frame)
    finally:
        capture.release()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", help="Image/video path or camera index; overrides config")
    args = parser.parse_args()
    source = args.source
    detector = Detector("best.pt")
    for _, detections in infer_source(detector, source):
        print({"detections": [item.as_dict() for item in detections]})


if __name__ == "__main__":
    main()
