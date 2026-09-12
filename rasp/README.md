# Raspberry Pi 4 SAR deployment bundle

Copy this entire `rasp` folder to the Raspberry Pi SD card or home directory. It contains only the CPU inference pipeline, optional LoRa support, and the portable trained model `runs/detect/afo_victim/weights/best.pt`.

It deliberately excludes datasets, tests, training, TensorRT, Jetson setup, `best.engine`, and `last.pt`. The model class remains `0 = victim`.

## Install on Raspberry Pi OS 64-bit

```bash
cd ~/rasp
sudo apt update
sudo apt install -y python3 python3-venv python3-pip libopenblas0 libatlas3-base libgl1
chmod +x setup_raspberry_pi.sh
./setup_raspberry_pi.sh
source .venv/bin/activate
```

No CUDA, TensorRT, JetPack, or NVIDIA dependency is installed.

## Configure

Edit `config/config.yaml` before running. The default model is CPU PyTorch:

```yaml
model_backend: pytorch
model_path: runs/detect/afo_victim/weights/best.pt
imgsz: 640
confidence: 0.35
iou: 0.5
device: cpu
frame_skip: 0
```

Set `paths.input_source: 0` for a camera or a path such as `media/search.mp4` for video. Set `serial.enabled: true` only after selecting the connected LoRa port, normally `/dev/ttyUSB0`.

## Run

```bash
# Camera or configured video source
python -m pipeline.run_pipeline --config config/config.yaml

# One image
python models/model2_detection/infer.py --config config/config.yaml --source /path/to/image.jpg

# One video
python models/model2_detection/infer.py --config config/config.yaml --source /path/to/video.mp4
```

Each result includes structured victim bounding boxes and a compact display/transmission value such as `30087_`. The five logical digits mean three victims with highest confidence 87%; `_` is the message delimiter.

## Optional NCNN

Try NCNN only after CPU PyTorch works:

```bash
python models/model2_detection/export_ncnn.py --config config/config.yaml
```

Point `model_path` to the created `*_ncnn_model` directory and set `model_backend: ncnn`. This does not modify `best.pt`.

Pi 4 CPU processing can be slow. Lower `imgsz`, increase `frame_skip`, and keep stitching resize/buffer settings conservative when necessary.
