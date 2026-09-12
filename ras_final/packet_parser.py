"""Parse a compact SAR packet received from the Raspberry Pi/LoRa side."""

from __future__ import annotations

import json
from typing import Any


def parse_packet(packet: str | bytes) -> dict[str, list[list[int]]]:
    text = packet.decode("utf-8") if isinstance(packet, bytes) else packet
    data = json.loads(text)
    victims = [[int(x), int(y)] for x, y in data.get("v", [])]
    path = [[int(x), int(y)] for x, y in data.get("p", [])]
    return {"v": victims, "p": path}



if __name__ == "__main__":
    sample = '{"v":[[120,200],[130,210]],"p":[[0,0],[1,0],[2,1]]}'
    print(parse_packet(sample))
