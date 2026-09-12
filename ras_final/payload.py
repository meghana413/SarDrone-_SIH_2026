"""Alternative reference protocol for compact SAR telemetry.

This module is kept as a historical/reference implementation only. It is not the
runtime format wired into ``ras_final.main``; the live Pi pipeline uses the
``[[persons],[path]]|CONFIDENCE`` format implemented in ``protocol.py``.
"""

from __future__ import annotations

import json
from typing import Iterable, Sequence

MAX_PACKET_BYTES = 512


def _as_point_list(points: Iterable[Sequence[int | float]]) -> list[list[int | float]]:
    return [[int(x), int(y)] for x, y in points]


def compact_json(value: object) -> str:
    return json.dumps(value, separators=(",", ":"), allow_nan=False)


def build_compact_payload(victims: Iterable[Sequence[int | float]], path: Iterable[Sequence[int | float]]) -> str:
    """Return a compact JSON payload with victims and path only.

    Example payload:
        {"v":[[120,200],[130,210]],"p":[[0,0],[1,0],[2,1]]}
    """
    victim_points = _as_point_list(victims)
    path_points = _as_point_list(path)

    payload = {"v": victim_points, "p": path_points}
    data = compact_json(payload).encode("utf-8")
    if len(data) <= MAX_PACKET_BYTES:
        return compact_json(payload)

    trimmed_path = path_points[:]
    while trimmed_path and len(compact_json({"v": victim_points, "p": trimmed_path}).encode("utf-8")) > MAX_PACKET_BYTES:
        trimmed_path.pop()

    if not trimmed_path:
        raise ValueError("payload too large even with empty path; reduce victim count")

    payload = {"v": victim_points, "p": trimmed_path}
    return compact_json(payload)


def parse_compact_payload(payload: str) -> dict[str, list[list[int]]]:
    """Reverse the compact payload format back into python lists."""
    parsed = json.loads(payload)
    victims = [[int(x), int(y)] for x, y in parsed.get("v", [])]
    path = [[int(x), int(y)] for x, y in parsed.get("p", [])]
    return {"v": victims, "p": path}


def ensure_within_limit(payload: str) -> None:
    if len(payload.encode("utf-8")) > MAX_PACKET_BYTES:
        raise ValueError(f"payload size {len(payload.encode('utf-8'))} exceeds {MAX_PACKET_BYTES} bytes")


if __name__ == "__main__":
    victims = [[120, 200], [130, 210]]
    path = [[0, 0], [1, 0], [2, 1], [2, 2], [3, 2]]
    packet = build_compact_payload(victims, path)
    ensure_within_limit(packet)
    print(packet)
    print(f"size_bytes={len(packet.encode('utf-8'))}")
