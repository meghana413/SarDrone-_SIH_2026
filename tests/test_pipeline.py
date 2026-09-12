"""Portable module tests; no camera or serial hardware is required."""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import pytest
import yaml

from comms.lora_send import LoRaSender
from models.model1_stitching.stitch import Stitcher
from models.model2_detection.infer import Detection, Detector, make_compact_output
from models.model3_pathfinding.astar import detections_to_cost_grid, find_path
from pipeline.run_pipeline import load_config


def record(confidence: float) -> dict[str, object]:
    return {"class_id": 0, "class_name": "victim", "confidence": confidence, "bbox": [1, 2, 3, 4]}


def test_config_loading() -> None:
    config = load_config("config/config.yaml")
    assert config["model_backend"] == "pytorch"
    assert config["device"] == "cpu"
    assert config["model_path"].endswith("best.pt")


@pytest.mark.parametrize(("detections", "expected"), [
    ([], "_00000"), ([record(0.91)], "_01091"),
    ([record(0.65), record(0.40)], "_02065"),
    ([record(0.08)] * 5, "_05008"),
    ([record(0.63), record(0.87), record(0.72)], "_03087"),
])
def test_compact_output_formats(detections: list[dict[str, object]], expected: str) -> None:
    result = make_compact_output(detections)
    assert result == expected
    assert isinstance(result, str) and len(result) == 6
    assert result.startswith("_") and result[1:].isdigit()


def test_detection_schema() -> None:
    output = Detection(1, 2, 3, 4, 0, "victim", 0.9).as_dict()
    assert output == {"class_id": 0, "class_name": "victim", "confidence": 0.9, "bbox": [1, 2, 3, 4]}


def test_detector_uses_cpu_and_configured_model() -> None:
    detector = Detector.from_config(load_config("config/config.yaml"))
    assert detector.device == "cpu" and detector.backend == "pytorch"


def test_detector_predicts_one_real_test_image() -> None:
    pytest.importorskip("ultralytics")
    config = load_config("config/config.yaml")
    image_path = next(Path("data/afo_small/images/test").glob("*.jpg"))
    image = cv2.imread(str(image_path))
    assert image is not None
    # Keep CI/laptop smoke testing fast; deployment still uses configured imgsz.
    detections = Detector(config["model_path"], config["confidence"], config["iou"], "cpu", "pytorch", 160).predict(image)
    assert isinstance(detections, list)
    assert all(item.class_id == 0 and item.class_name == "victim" and len(item.bbox) == 4 for item in detections)


def test_stitcher_validation_and_resize() -> None:
    with pytest.raises(ValueError, match="at least two"):
        Stitcher()([np.zeros((10, 10, 3), dtype=np.uint8)])
    assert Stitcher(resize_width=100).resize_width == 100


def test_astar_and_detection_grid() -> None:
    grid = [[0.0] * 5 for _ in range(5)]
    grid[2][1:4] = [float("inf")] * 3
    path = find_path(grid, (0, 0), (4, 4))
    assert path[0] == (0, 0) and path[-1] == (4, 4)
    victim_grid = detections_to_cost_grid([record(0.9)], (4, 4))
    assert len(victim_grid) == 4
    assert victim_grid[0][0] == 0.0
    assert any(cell >= 100.0 for row in victim_grid for cell in row)


def test_astar_plans_toward_detected_victim() -> None:
    victim = {"class_name": "victim", "bbox": [0.0, 0.0, 2.0, 2.0]}
    grid = detections_to_cost_grid([victim], (4, 4))
    assert grid[1][1] == 100.0
    assert any(cell >= 100.0 for row in grid for cell in row)

    grid2 = detections_to_cost_grid([{"class_name": "victim", "bbox": [0.0, 0.0, 0.5, 0.5]}], (4, 4))
    assert grid2[0][0] == 100.0


def test_lora_without_hardware() -> None:
    sender = LoRaSender(port="/dev/ttyUSB0")
    assert sender.encode({"event": "test", "gps": [1.0, 2.0]})[:4] == b"SAR1"
    with pytest.raises(ValueError):
        sender.send_compact("123")
    assert LoRaSender.send_compact.__defaults__ == (b"_",)
