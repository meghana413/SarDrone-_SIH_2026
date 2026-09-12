# SAR Drone Pipeline — Raspberry Pi 4

This runs the existing one-class YOLO11n victim detector (`0 = victim`) with OpenCV stitching, A* planning, and optional LoRa. It supports laptop development and Raspberry Pi 4 (4 GB, Raspberry Pi OS 64-bit). Inference is CPU-only: no CUDA, TensorRT, JetPack, NVIDIA software, or Jetson GPIO is required.

`runs/detect/afo_victim/weights/best.pt` is the portable trained model and is never modified. `best.engine` is a Jetson/TensorRT artifact and must not be used on Raspberry Pi.

## Install

Python 3.9+ and a 64-bit OS are required. On a laptop (PowerShell):

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -r requirements-training.txt
```

On Raspberry Pi OS 64-bit, copy/clone the repository including `best.pt`, then:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip libopenblas0 libatlas3-base libgl1
chmod +x setup_raspberry_pi.sh
./setup_raspberry_pi.sh
source .venv/bin/activate
```

The setup script installs no CUDA, TensorRT, JetPack, or NVIDIA packages.

## Configuration

Edit [config/config.yaml](config/config.yaml):

```yaml
model_backend: pytorch
model_path: runs/detect/afo_victim/weights/best.pt
imgsz: 640
confidence: 0.35
iou: 0.5
device: cpu
frame_skip: 0
```

Set `paths.input_source` to `0` for a USB camera (or a Pi camera exposed through OpenCV), or to a video path. `frame_skip` avoids inference on intermediate frames. `stitching.resize_width`, `interval_frames`, `min_frames`, and `max_buffer_frames` control CPU/RAM use. Enable `pipeline.display` only where a display is available.

## Run inference

One image:

```bash
python models/model2_detection/infer.py --config config/config.yaml --source data/afo_small/images/test/a_1015_jpg.rf.762130bfa4444f6be54290f7a8e40f55.jpg
```

Recorded video:

```bash
python models/model2_detection/infer.py --config config/config.yaml --source path/to/video.mp4
```

Camera:

```bash
python models/model2_detection/infer.py --config config/config.yaml --source 0
```

Full pipeline (set `paths.input_source` first):

```bash
python -m pipeline.run_pipeline --config config/config.yaml
```

Each detection is `{"class_id": 0, "class_name": "victim", "confidence": 0.91, "bbox": [x1, y1, x2, y2]}`. The logical compact value is exactly `DCCCC`: first digit count (0–9), final four digits zero-padded highest-confidence percentage. Three victims with highest confidence `0.87` yields `"30087"`; no detection yields `"00000"`. Command output and LoRa transmission append `_` as a delimiter, so the receiver sees `"30087_"` or `"00000_"`.

## Optional NCNN

NCNN is worth trying when CPU PyTorch is too slow, but is not required initially. This creates a new exported directory without changing `best.pt`:

```bash
python models/model2_detection/export_ncnn.py --config config/config.yaml
```

Install any exporter/runtime dependencies reported by your installed Ultralytics version, then set `model_backend: ncnn` and `model_path` to the resulting `*_ncnn_model` directory. The same interface supports an ONNX model using `model_backend: onnx`.

## LoRa, training, and tests

LoRa is disabled by default. Set `serial.enabled: true` and use a real port such as `/dev/ttyUSB0` (or a laptop COM port). If unavailable, the pipeline continues without telemetry.

Training is optional and not a Pi deployment requirement. `export_tensorrt.py` remains only as a marked NVIDIA/Jetson legacy tool; the main pipeline never calls it.

```bash
python -m pytest -q
```

Tests need no camera or LoRa. With Ultralytics installed they run `best.pt` on one bundled image. Pi 4 CPU inference/stitching may be slow; use a smaller `imgsz`, frame skipping, resized stitching inputs, cooling, and sequential processing. No real-time rate is promised.
# SarDrone-_SIH_2026
