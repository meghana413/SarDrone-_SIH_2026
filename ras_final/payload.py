"""Compact JSON telemetry payloads for the Raspberry Pi SAR runtime.

The on-air application payload is always ``{"v":[...],"p":[...]}``, where
``v`` contains victim grid coordinates and ``p`` contains the planned route.
"""

from __future__ import annotations

import json
from typing import Iterable, Sequence

MAX_PACKET_BYTES = 512


def format_confidence(confidence: float) -> str:
    """Format a normalized YOLO confidence as a zero-padded percentage.

    YOLO returns values in the range 0.0--1.0, so 0.875 becomes ``"087"``
    when truncated as requested for the telemetry display.  The confidence is
    deliberately not added to the documented ``v``/``p`` payload schema.
    """
    value = max(0.0, min(1.0, float(confidence)))
    return f"{int(value * 100):03d}"


def _as_point_list(points: Iterable[Sequence[int | float]]) -> list[list[int]]:
    result: list[list[int]] = []
    for point in points:
        if len(point) != 2:
            raise ValueError(f"coordinate must contain two values: {point!r}")
        result.append([int(point[0]), int(point[1])])
    return result


def compact_json(value: object) -> str:
    return json.dumps(value, separators=(",", ":"), allow_nan=False)


def build_compact_payload(victims: Iterable[Sequence[int | float]], path: Iterable[Sequence[int | float]]) -> str:
    """Build a <=512-byte ``{"v": ..., "p": ...}`` payload.

    When a complete route is too large, retain its prefix (which includes the
    vehicle's current position) and trim only trailing route cells.
    """
    victim_points = _as_point_list(victims)
    path_points = _as_point_list(path)
    payload = {"v": victim_points, "p": path_points}

    while len(compact_json(payload).encode("utf-8")) > MAX_PACKET_BYTES and path_points:
        path_points.pop()
        payload["p"] = path_points
    if len(compact_json(payload).encode("utf-8")) > MAX_PACKET_BYTES:
        raise ValueError("payload is too large even without a path; reduce victim count")
    return compact_json(payload)


def parse_compact_payload(payload: str | bytes) -> dict[str, list[list[int]]]:
    text = payload.decode("utf-8") if isinstance(payload, bytes) else payload
    parsed = json.loads(text)
    if not isinstance(parsed, dict) or set(parsed) != {"v", "p"}:
        raise ValueError("payload must contain exactly the 'v' and 'p' fields")
    return {"v": _as_point_list(parsed["v"]), "p": _as_point_list(parsed["p"])}


def ensure_within_limit(payload: str) -> None:
    size = len(payload.encode("utf-8"))
    if size > MAX_PACKET_BYTES:
        raise ValueError(f"payload size {size} exceeds {MAX_PACKET_BYTES} bytes")
