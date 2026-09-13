"""Deterministic smoke test for the grid-string runtime protocol."""

from __future__ import annotations

import json
import sys
from pathlib import Path

script_dir = Path(__file__).resolve().parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

if __package__ in (None, ""):
    from protocol import serialize_result
else:
    from ras_final.protocol import serialize_result


def run_test_mode() -> None:
    message = serialize_result([[5, 8], [17, 21]], [[0, 0], [1, 0], [2, 0]], 98.7)
    if not message.endswith("|987"):
        raise AssertionError("wrong confidence scaling in serialized message")
    print(json.dumps({"message": message, "grid_points": [[5, 8], [17, 21]], "path": [[0, 0], [1, 0], [2, 0]]}, separators=(",", ":")))
