"""Optionally export the portable PyTorch checkpoint to an NCNN model."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml


def export_ncnn(config_path: str | Path = "config/config.yaml") -> Any:
    """Export ``model_path`` to NCNN without changing the source checkpoint."""
    with Path(config_path).open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    from ultralytics import YOLO

    weights = config["model_path"]
    result = YOLO(weights).export(format="ncnn", imgsz=config["imgsz"])
    print(f"NCNN model exported from {weights}: {result}")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config/config.yaml")
    export_ncnn(parser.parse_args().config)
