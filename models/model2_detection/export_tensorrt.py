"""Legacy NVIDIA/Jetson-only TensorRT exporter; not used by the Pi pipeline."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml


def export_engine(config_path: str | Path = "config/config.yaml") -> Any:
    """Build a TensorRT engine only on a compatible NVIDIA/Jetson host."""
    with Path(config_path).open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    from ultralytics import YOLO

    weights = config.get("model_path", config["paths"].get("model_weights"))
    if not weights:
        raise ValueError("a PyTorch model path is required")
    model = YOLO(weights)
    result = model.export(
        format="engine",
        half=True,
        imgsz=config.get("imgsz", config["model"]["image_size"]),
        device=config.get("device", config["model"]["device"]),
        workspace=4,
    )
    print(f"TensorRT FP16 engine exported from {weights}: {result}. This is not portable to Raspberry Pi.")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config/config.yaml")
    export_engine(parser.parse_args().config)
