"""Raspberry Pi SAR pipeline using the existing project models.

The runtime keeps the 3-model flow:
    Camera -> Model 1 stitch -> Model 2 detection -> Model 3 A* -> compact result
"""

from __future__ import annotations

import json
import logging
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np

from .camera import CameraSource
from .payload import build_compact_payload, format_confidence

from .models.model1_stitching.stitch import Stitcher
from .models.model2_detection.infer import Detector
from .models.model3_pathfinding.astar import detections_to_cost_grid, find_path, victim_cells_from_detections

logger = logging.getLogger(__name__)

GRID_SIZE = 32
GRID_MAX = GRID_SIZE - 1


def _map_pixel_to_grid(x: float, y: float, frame_w: int, frame_h: int, grid_size: int = GRID_SIZE) -> tuple[int, int]:
    if frame_w <= 0 or frame_h <= 0:
        raise ValueError("frame dimensions must be positive")
    x_index = int(round((x / frame_w) * (grid_size - 1)))
    y_index = int(round((y / frame_h) * (grid_size - 1)))
    x_index = max(0, min(grid_size - 1, x_index))
    y_index = max(0, min(grid_size - 1, y_index))
    return x_index, y_index


@dataclass
class ScanResult:
    persons: list[list[int]] = field(default_factory=list)
    path: list[list[int]] = field(default_factory=list)
    confidence: float = 0.0
    payload: str = ""


class SARPiPipeline:
    """End-to-end pipeline for Raspberry Pi runtime."""

    def __init__(self, source: str | int | None = None, weights: str | Path | None = None,
                 confidence: float = 0.35, iou: float = 0.5, imgsz: int = 640,
                 queue_size: int = 4) -> None:
        self.camera = CameraSource(source=source)
        self.stitcher = Stitcher(resize_width=960)
        if weights is None:
            default_weights = Path(__file__).resolve().parent / "weights" / "best.pt"
            self.weights = str(default_weights)
        else:
            self.weights = str(weights)
        self.detector = Detector(self.weights, confidence=confidence, iou=iou, device="cpu", backend="pytorch", imgsz=imgsz)
        self.current_result = ScanResult()
        self.next_result = ScanResult()
        self._lock = threading.Lock()
        self._generation_thread: threading.Thread | None = None
        self._scan_cycle = 0
        self.queue_size = queue_size

    def prepare_frame(self, frames: Iterable[np.ndarray]) -> np.ndarray:
        frame_list = list(frames)
        if not frame_list:
            raise ValueError("no frames available")
        if len(frame_list) >= 2:
            try:
                return self.stitcher(frame_list)
            except RuntimeError:
                logger.warning("stitching failed, falling back to single frame")
                return frame_list[-1]
        return frame_list[0]

    def detect_and_plan(self, frame: np.ndarray) -> ScanResult:
        detections = self.detector.predict(frame)
        logger.info("Detections: %d", len(detections))
        for detection in detections:
            logger.info("Detected person: class=%s conf=%.3f bbox=%s", detection.class_name, detection.confidence, detection.bbox)

        persons = []
        conf_values = []
        for detection in detections:
            if detection.class_name.lower() != "victim":
                continue
            conf_values.append(float(detection.confidence))

        victim_cells = victim_cells_from_detections(detections, (GRID_SIZE, GRID_SIZE), frame_shape=frame.shape[:2])
        persons = [[column, row] for row, column in victim_cells]
        cost_grid = detections_to_cost_grid(detections, (GRID_SIZE, GRID_SIZE), frame_shape=frame.shape[:2])
        if persons:
            goal = min(victim_cells, key=lambda cell: abs(cell[0]) + abs(cell[1]))
            path = find_path(cost_grid, (0, 0), goal)
            if not path:
                path = find_path(cost_grid, (0, 0), (GRID_MAX, GRID_MAX))
        else:
            path = find_path(cost_grid, (0, 0), (GRID_MAX, GRID_MAX))
        path_points = [[x, y] for x, y in [(col, row) for row, col in path]]

        confidence = sum(conf_values) / len(conf_values) if conf_values else 0.0
        if not persons:
            confidence = 0.0

        payload = build_compact_payload(persons, path_points)
        logger.info("Payload length: %d bytes; path length: %d; persons: %d",
                    len(payload.encode("utf-8")), len(path_points), len(persons))
        logger.info("Confidence: %s", format_confidence(confidence))

        return ScanResult(persons=persons, path=path_points, confidence=confidence, payload=payload)

    def run_cycle(self) -> ScanResult:
        frames = self.camera.read_many(count=2)
        if not frames:
            raise RuntimeError("No frame captured for scan cycle")
        frame = self.prepare_frame(frames)
        result = self.detect_and_plan(frame)
        self._scan_cycle += 1
        logger.info("Completed cycle %d", self._scan_cycle)
        return result

    def generate_next_async(self) -> None:
        def worker() -> None:
            try:
                result = self.run_cycle()
                with self._lock:
                    self.next_result = result
            except Exception as exc:  # pragma: no cover - runtime failure path.
                logger.exception("Background scan generation failed: %s", exc)
                with self._lock:
                    self.next_result = ScanResult()
        self._generation_thread = threading.Thread(target=worker, daemon=True)
        self._generation_thread.start()

    def swap_if_ready(self) -> bool:
        if self._generation_thread is None or self._generation_thread.is_alive():
            return False
        with self._lock:
            self.current_result = self.next_result
            self.next_result = ScanResult()
        return True


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    pipeline = SARPiPipeline(source=None)
    try:
        result = pipeline.run_cycle()
        print(json.dumps({"persons": result.persons, "path": result.path, "confidence": result.confidence, "payload": result.payload}))
    finally:
        pipeline.camera.close()
