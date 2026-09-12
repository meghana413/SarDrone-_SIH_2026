"""Protocol helpers for the Raspberry Pi SAR pipeline.

This project uses the existing 32x32 logical grid defined by the A* planner and
by the runtime call that creates the cost grid as (32, 32).

The A* implementation in the project indexes cells as (row, column), but the
serialized Pi payload exposes them as (x, y) = (column, row) to keep the same
32x32 map coordinates consistent throughout the pipeline.

Message format:
    JSON_DATA|CONFIDENCE

where JSON_DATA is a compact JSON list:
    [[person_coords], [shortest_path]]

and CONFIDENCE is a 3-character confidence value encoded as percentage * 10.
"""

from __future__ import annotations

import json
from typing import Iterable, Sequence

GRID_SIZE = 32
GRID_MAX = GRID_SIZE - 1
MAX_CHUNK_CHARS = 253


def clamp_point(point: Sequence[int | float]) -> list[int]:
    if len(point) != 2:
        raise ValueError(f"point must contain exactly 2 values: {point!r}")
    x = int(round(float(point[0])))
    y = int(round(float(point[1])))
    if not (0 <= x <= GRID_MAX and 0 <= y <= GRID_MAX):
        raise ValueError(f"point out of range for 32x32 grid: {(x, y)}")
    return [x, y]


def normalize_persons(persons: Iterable[Sequence[int | float]]) -> list[list[int]]:
    return [clamp_point(point) for point in persons]


def normalize_path(path: Iterable[Sequence[int | float]]) -> list[list[int]]:
    return [clamp_point(point) for point in path]


def mean_confidence(confidences: Iterable[float]) -> float:
    confs = [float(value) for value in confidences]
    if not confs:
        return 0.0
    return sum(confs) / len(confs)


def format_confidence(confidence: float | int) -> str:
    value = float(confidence)
    if not value or value < 0:
        return "000"
    percentage = max(0.0, min(100.0, value)) * 10.0
    return f"{int(round(percentage)):03d}"


def serialize_result(persons: Iterable[Sequence[int | float]], path: Iterable[Sequence[int | float]], confidence: float | int) -> str:
    payload = [normalize_persons(persons), normalize_path(path)]
    json_data = json.dumps(payload, separators=(",", ":"), allow_nan=False)
    return f"{json_data}|{format_confidence(confidence)}"


def parse_serialized_message(message: str) -> tuple[list[list[list[int]]], str]:
    if "|" not in message:
        raise ValueError("message must contain JSON payload and confidence delimiter '|'")
    json_part, conf_part = message.rsplit("|", 1)
    payload = json.loads(json_part)
    if not isinstance(payload, list) or len(payload) != 2:
        raise ValueError("message payload must contain [persons, path]")
    persons = [[int(x), int(y)] for x, y in payload[0]]
    path = [[int(x), int(y)] for x, y in payload[1]]
    if len(conf_part) != 3 or not conf_part.isdigit():
        raise ValueError("confidence field must be exactly 3 digits")
    return [persons, path], conf_part


def chunk_message(message: str, message_id: str = "SAR", max_chars: int = MAX_CHUNK_CHARS) -> list[str]:
    if not message:
        raise ValueError("message cannot be empty")
    total = len(message)
    header_template = f"{message_id}|{{index}}|{{total}}|"
    if total <= max_chars:
        return [f"{header_template.format(index=1, total=1)}{message}"]

    overhead = len(header_template.format(index=1, total=1))
    payload_limit = max_chars - overhead
    if payload_limit <= 0:
        raise ValueError("chunk size too small for protocol header")

    total_chunks = (total + payload_limit - 1) // payload_limit
    chunks: list[str] = []
    for index in range(total_chunks):
        start = index * payload_limit
        end = start + payload_limit
        payload = message[start:end]
        chunk = header_template.format(index=index + 1, total=total_chunks) + payload
        if len(chunk) > max_chars:
            raise ValueError(f"chunk exceeded {max_chars} characters: {len(chunk)}")
        chunks.append(chunk)
    return chunks


def reconstruct_message(chunks: Iterable[str]) -> str:
    ordered = sorted(chunks, key=lambda item: _chunk_index(item))
    message_parts: list[str] = []
    for chunk in ordered:
        payload = _payload_from_chunk(chunk)
        message_parts.append(payload)
    return "".join(message_parts)


def frame_serial_message(message: str, prefix: str = "PI2ESP") -> str:
    """Wrap a complete serialized message for a UART transfer to the ESP32.

    The framed format is:
        PI2ESP|<length>|<message>
    where ``length`` is the exact byte length of the original serialized message.
    This allows the ESP32 to reconstruct the original message before LoRa transmission.
    """
    payload = message.encode("utf-8")
    return f"{prefix}|{len(payload)}|{message}"


def unframe_serial_message(frame: str, prefix: str = "PI2ESP") -> str:
    """Decode a UART frame sent from the Raspberry Pi to the ESP32."""
    if not frame.startswith(f"{prefix}|"):
        raise ValueError(f"frame must start with {prefix}|")
    _, length_text, payload = frame.split("|", 2)
    if not length_text.isdigit():
        raise ValueError("payload length header must be numeric")
    expected = int(length_text)
    actual = len(payload.encode("utf-8"))
    if actual != expected:
        raise ValueError(f"payload length mismatch: expected {expected}, got {actual}")
    return payload


def _chunk_index(chunk: str) -> int:
    try:
        _, index, _, _ = chunk.split("|", 3)
        return int(index)
    except (ValueError, TypeError):
        raise ValueError(f"invalid chunk format: {chunk!r}")


def _payload_from_chunk(chunk: str) -> str:
    try:
        _, _, _, payload = chunk.split("|", 3)
        return payload
    except ValueError as exc:
        raise ValueError(f"invalid chunk format: {chunk!r}") from exc


if __name__ == "__main__":
    sample = serialize_result([[5, 8], [17, 21]], [[0, 0], [1, 0], [2, 0]], 98.7)
    print(sample)
    print(chunk_message(sample))
