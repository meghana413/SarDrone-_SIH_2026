# Raspberry Pi final payload format

## Deploy on Raspberry Pi 4

1. Copy this folder to the Raspberry Pi 4 as a standalone deployable package.
2. The tracked `ras_final/weights/.gitkeep` creates the weights directory on a fresh clone. Put the YOLO model file named `best.pt` into `~/ras_final/weights/`.
3. Set up the local environment from inside the `ras_final/` folder:
   ```bash
   cd ~/ras_final
   ./setup_pi.sh
   ```
4. Connect the first ESP32 to the Pi UART pins and confirm the serial port name with:
   ```bash
   ls /dev/ttyUSB*
   ls /dev/ttyACM*
   ```
5. Run continuous mode from the parent directory of `ras_final/`:
   ```bash
   cd ~
   python -m ras_final.main --serial-port /dev/ttyUSB0
   ```
   or a single scan/send:
   ```bash
   cd ~
   python -m ras_final.main --serial-port /dev/ttyUSB0 --once
   ```
6. Optional: install the service for auto-start on boot:
   ```bash
   sudo cp ~/ras_final/ras_final.service /etc/systemd/system/
   sudo systemctl enable --now ras_final
   ```

This folder is designed to run by itself on Raspberry Pi 4 without depending on sibling project folders.

## Format used

The runtime used by `main.py` -> `pipeline.py` -> `payload.build_compact_payload()` emits compact JSON:

```json
{"v":[{"x":5,"y":8},{"x":17,"y":21}],"p":[[0,0],[1,0],[2,0]]}
```

where:

- `v` is a list of victim coordinate objects, each with integer `x` and `y` values on the 32 x 32 logical grid.
- `p` is the safe route as `[x, y]` grid cells, from the origin to a detected victim.

YOLO confidence remains normalized (`0.0`--`1.0`) internally. Where a three-digit display value is needed, it is formatted with `int(confidence * 100)`, so `0.875` becomes `087` rather than `000`.

This JSON text is what the Pi transmits over UART before the ESP32 forwards it by LoRa.

## Important project constraints

- path grid size used by Model 3: 32 x 32
- LoRa packet limit in this project: 512 bytes
- we use compact JSON with no spaces to keep payload small
- if the payload is above the limit, the path is trimmed from the end until it fits
