"""Example: send a compact victim+path payload from Raspberry Pi."""

from __future__ import annotations

from payload import build_compact_payload, ensure_within_limit
from lora_sender import LoRaSender


def main() -> None:
    victims = [[120, 200], [130, 210]]
    path = [[0, 0], [1, 0], [2, 1], [2, 2], [3, 2]]

    payload = build_compact_payload(victims, path)
    ensure_within_limit(payload)

    sender = LoRaSender(port="/dev/ttyUSB0")
    packet = {"v": victims, "p": path}
    sender.send(packet)
    print("Sent compact SAR packet:")
    print(payload)
    print(f"Bytes={len(payload.encode('utf-8'))}")


if __name__ == "__main__":
    main()
