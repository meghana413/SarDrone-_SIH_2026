# Raspberry Pi final payload format

## Deploy on Raspberry Pi 4

1. Copy this folder to the Raspberry Pi 4 as a standalone deployable package.
2. Put the YOLO model file named `best.pt` into `ras_final/weights/`.
3. Run:
   ```bash
   cd ~/ras_final
   ./setup_pi.sh
   ```
4. Connect the first ESP32 to the Pi UART pins and confirm the serial port name with:
   ```bash
   ls /dev/ttyUSB*
   ls /dev/ttyACM*
   ```
5. Run continuous mode:
   ```bash
   python -m ras_final.main --serial-port /dev/ttyUSB0
   ```
   or a single scan/send:
   ```bash
   python -m ras_final.main --serial-port /dev/ttyUSB0 --once
   ```
6. Optional: install the service for auto-start on boot:
   ```bash
   sudo cp ras_final/ras_final.service /etc/systemd/system/
   sudo systemctl enable --now ras_final
   ```

This folder is designed to run by itself on Raspberry Pi 4 without depending on sibling project folders.

## Format used

We send only:

- victims: a list of victim coordinates in pixel/grid space
- path: the safest route coordinates in grid space

Example payload:

```json
{
  "v": [
    [120, 200],
    [130, 210]
  ],
  "p": [
    [0, 0],
    [1, 0],
    [2, 1]
  ]
}
```

This removes GPS values to reduce size and works better with LoRa.

## Important project constraints

- path grid size used by Model 3: 32 x 32
- LoRa packet limit in this project: 512 bytes
- we use compact JSON with no spaces to keep payload small
- if the payload is above the limit, the path is trimmed from the end until it fits

## Files

- `payload.py` - builds and validates compact payloads
- `lora_sender.py` - serial LoRa packet sender
- `example_send.py` - example sender using the final compact format
- `packet_parser.py` - parse the received compact payload back into lists

## Example use

```python
from payload import build_compact_payload

victims = [[120, 200], [130, 210]]
path = [[0, 0], [1, 0], [2, 1], [2, 2], [3, 2]]
packet = build_compact_payload(victims, path)
print(packet)
```

This returns a JSON string that can be sent over LoRa.
