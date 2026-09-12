"""Run CPU detection, periodic stitching, A*, and optional LoRa telemetry."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import cv2
import yaml

from comms.lora_send import LoRaSender
from models.model1_stitching.stitch import Stitcher
from models.model2_detection.infer import Detector, _source_value, make_compact_output
from models.model3_pathfinding.astar import detections_to_cost_grid, find_path


def load_config(path: str | Path) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def run(config_path: str | Path = "config/config.yaml") -> None:
    config = load_config(config_path)
    paths, pipeline, stitching_config = config["paths"], config["pipeline"], config["stitching"]
    results_dir = Path(paths["results_dir"])
    results_dir.mkdir(parents=True, exist_ok=True)
    detector = Detector.from_config(config)
    stitcher = Stitcher(resize_width=stitching_config.get("resize_width"))
    source = _source_value(paths["input_source"])
    image_suffixes = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    single_frame = None
    capture = None
    if isinstance(source, str) and Path(source).suffix.lower() in image_suffixes:
        single_frame = cv2.imread(source)
        if single_frame is None:
            raise OSError(f"unable to read image source {source!r}")
    else:
        capture = cv2.VideoCapture(source)
        if not capture.isOpened():
            capture.release()
            raise OSError(f"unable to open camera/video source {source!r}")
    serial_config = config["serial"]
    sender = LoRaSender(**{key: value for key, value in serial_config.items() if key != "enabled"})
    frames, frame_index = [], 0
    try:
        while True:
            if single_frame is not None:
                frame, single_frame = single_frame, None
            else:
                assert capture is not None
                ok, frame = capture.read()
                if not ok:
                    break
            if frame is None:
                break
            frame_index += 1
            if config.get("frame_skip", 0) and (frame_index - 1) % (config["frame_skip"] + 1):
                continue
            frames.append(frame)
            max_buffer = stitching_config.get("max_buffer_frames", stitching_config["interval_frames"])
            if len(frames) > max_buffer:
                frames.pop(0)
            detections = detector.predict(frame)
            compact = make_compact_output(detections)
            cost_grid = detections_to_cost_grid(detections, (32, 32))
            cells = find_path(cost_grid, (0, 0), (31, 31))
            waypoints = [[pipeline["gps_origin"][0], pipeline["gps_origin"][1], row, column] for row, column in cells]
            if serial_config.get("enabled", False) and frame_index % pipeline["send_every_n_frames"] == 0:
                try:
                    sender.send_event("detections", pipeline["gps_origin"], [item.as_dict() for item in detections], waypoints)
                    sender.send_compact(compact)  # Sender appends the '_' delimiter.
                except OSError as error:
                    print(f"LoRa unavailable ({error}); continuing without telemetry.")
                    serial_config["enabled"] = False
            interval = stitching_config["interval_frames"]
            if frame_index % interval == 0 and len(frames) >= stitching_config["min_frames"]:
                try:
                    cv2.imwrite(str(results_dir / "latest_panorama.jpg"), stitcher(frames))
                except RuntimeError:
                    pass
                frames.clear()
            print({"detections": [item.as_dict() for item in detections], "compact": compact})
            if pipeline.get("display", False):
                cv2.imshow("SAR drone", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
            if capture is None:  # A still-image source is processed once.
                break
    finally:
        sender.close()
        if capture is not None:
            capture.release()
        if pipeline.get("display", False):
            cv2.destroyAllWindows()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config/config.yaml")
    run(parser.parse_args().config)
