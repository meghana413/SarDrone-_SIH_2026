"""Send one documented compact SAR payload from the project root.

Run with ``python -m ras_final.example_send --serial-port /dev/ttyUSB0``.
"""

from __future__ import annotations

import argparse

from ras_final.lora_sender import LoRaSender
from ras_final.payload import build_compact_payload, ensure_within_limit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serial-port", default="/dev/ttyUSB0")
    parser.add_argument("--baudrate", type=int, default=115200)
    args = parser.parse_args()

    payload = build_compact_payload([[12, 20], [13, 21]], [[0, 0], [1, 0], [2, 1]])
    ensure_within_limit(payload)
    sender = LoRaSender(args.serial_port, args.baudrate)
    try:
        sender.send_text(payload)
    finally:
        sender.close()
    print(payload)


if __name__ == "__main__":
    main()
