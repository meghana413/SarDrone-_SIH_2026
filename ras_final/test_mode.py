"""Deterministic test mode for the SAR protocol and pipeline."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ras_final.protocol import chunk_message, parse_serialized_message, reconstruct_message, serialize_result

logger = logging.getLogger(__name__)


def run_test_mode() -> None:
    persons = [[5, 8], [17, 21], [25, 11]]
    path = [[0, 0], [1, 0], [2, 0], [2, 1], [3, 1], [4, 1]]
    confidence = 98.7
    message = serialize_result(persons, path, confidence)
    chunks = chunk_message(message, message_id="TEST")

    logger.info("Serialized message: %s", message)
    logger.info("Chunk count: %d", len(chunks))
    logger.info("Chunk size max: %d", max(len(chunk) for chunk in chunks))

    reconstructed = reconstruct_message(chunks)
    if reconstructed != message:
        raise AssertionError("reconstructed message does not match original message")

    parsed_data, conf = parse_serialized_message(message)
    if conf != "987":
        raise AssertionError(f"confidence mismatch: expected 987, got {conf}")
    assert parsed_data[0] == [[5, 8], [17, 21], [25, 11]]
    assert parsed_data[1] == [[0, 0], [1, 0], [2, 0], [2, 1], [3, 1], [4, 1]]

    print(json.dumps({
        "message": message,
        "chunks": len(chunks),
        "max_chunk_chars": max(len(chunk) for chunk in chunks),
        "reconstructed_match": reconstructed == message,
    }, separators=(",", ":")))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    run_test_mode()
