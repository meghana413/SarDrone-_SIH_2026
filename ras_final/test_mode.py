"""Small deterministic smoke test for the compact runtime payload."""

from __future__ import annotations

import json

from ras_final.packet_parser import parse_packet
from ras_final.payload import build_compact_payload, format_confidence


def run_test_mode() -> None:
    payload = build_compact_payload([[5, 8], [17, 21]], [[0, 0], [1, 0], [2, 0]])
    parsed = parse_packet(payload)
    if parsed["v"] != [{"x": 5, "y": 8}, {"x": 17, "y": 21}] or parsed["p"][-1] != [2, 0]:
        raise AssertionError("compact payload round-trip failed")
    if format_confidence(0.875) != "087":
        raise AssertionError("normalized confidence formatting failed")
    print(json.dumps({"payload": payload, "confidence": format_confidence(0.875)}, separators=(",", ":")))
