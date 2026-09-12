# Raspberry Pi final payload format

## Deploy on Raspberry Pi 4

1. Copy this folder to the Raspberry Pi 4 as a standalone deployable package.
2. Put the YOLO model file named `best.pt` into `~/ras_final/weights/`.
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

The runtime used by `main.py` -> `pipeline.py` -> `protocol.serialize_result()` emits a compact wire format of the form:

```text
[persons, path]|CONFIDENCE
```

where:

- `persons` is a list of victim grid coordinates, each as `[x, y]` on a 32 x 32 logical grid
- `path` is the safe route as a list of `[x, y]` grid cells, starting from the origin and ending at the selected goal
- `CONFIDENCE` is a three-digit number equal to `round(percentage * 10)`

Example:

```text
[[[5,8],[17,21]],[[0,0],[1,0],[2,0]]]|987
```

This means:

- victims: `[[5, 8], [17, 21]]`
- path: `[[0, 0], [1, 0], [2, 0]]`
- confidence: `98.7%`, encoded as `987`

This is the format emitted by `protocol.serialize_result()` and is what the Pi transmits over UART before the ESP32 forwards it by LoRa.

## Important project constraints

- path grid size used by Model 3: 32 x 32
- LoRa packet limit in this project: 512 bytes
- we use compact JSON with no spaces to keep payload small
- if the payload is above the limit, the path is trimmed from the end until it fits
