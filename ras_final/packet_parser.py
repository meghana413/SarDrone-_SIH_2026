"""Receiver-side parser for the documented compact SAR JSON payload."""

from __future__ import annotations

from .payload import parse_compact_payload


def parse_packet(packet: str | bytes) -> dict[str, list[list[int]]]:
    return parse_compact_payload(packet)
