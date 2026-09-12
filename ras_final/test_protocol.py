from __future__ import annotations

from types import SimpleNamespace

import numpy as np

from ras_final.pipeline import SARPiPipeline
from ras_final.protocol import chunk_message, frame_serial_message, parse_serialized_message, reconstruct_message, serialize_result, unframe_serial_message


def test_detect_and_plan_uses_percentage_confidence() -> None:
    pipeline = SARPiPipeline.__new__(SARPiPipeline)
    pipeline.detector = SimpleNamespace(
        predict=lambda frame: [
            SimpleNamespace(class_name="victim", confidence=0.875, bbox=[0.0, 0.0, 10.0, 10.0], x1=0.0, x2=10.0, y1=0.0, y2=10.0)
        ]
    )

    result = pipeline.detect_and_plan(np.zeros((32, 32, 3), dtype=np.uint8))

    assert result.confidence == 87.5
    assert result.serialized.endswith("|875")


def test_detect_and_plan_targets_detected_victim_cell() -> None:
    pipeline = SARPiPipeline.__new__(SARPiPipeline)
    pipeline.detector = SimpleNamespace(
        predict=lambda frame: [
            SimpleNamespace(class_name="victim", confidence=0.9, bbox=[12.0, 8.0, 8.0, 8.0], x1=12.0, x2=20.0, y1=8.0, y2=16.0)
        ]
    )

    result = pipeline.detect_and_plan(np.zeros((32, 32, 3), dtype=np.uint8))

    assert result.path
    assert result.path[-1] == result.persons[0]
    assert result.path[-1] != [31, 31]


def test_serialize_and_parse_round_trip() -> None:
    persons = [[5, 8], [17, 21], [25, 11]]
    path = [[0, 0], [1, 0], [2, 0], [2, 1], [3, 1], [4, 1]]
    message = serialize_result(persons, path, 98.7)
    parsed, conf = parse_serialized_message(message)

    assert parsed[0] == persons
    assert parsed[1] == path
    assert conf == "987"


def test_chunk_reconstruction_matches_original() -> None:
    persons = [[5, 8], [17, 21]]
    path = [[0, 0], [1, 0], [2, 0], [2, 1], [3, 1], [4, 1], [5, 1], [6, 1]]
    message = serialize_result(persons, path, 12.5)
    chunks = chunk_message(message, message_id="TST")

    assert all(len(chunk) <= 253 for chunk in chunks)
    assert reconstruct_message(chunks) == message


def test_confidence_zero_and_no_persons() -> None:
    message = serialize_result([], [[0, 0], [1, 0]], 0.0)
    parsed, conf = parse_serialized_message(message)

    assert parsed[0] == []
    assert parsed[1] == [[0, 0], [1, 0]]
    assert conf == "000"


def test_confidence_fraction_is_encoded_as_percentage() -> None:
    confidence_percent = 0.875 * 100.0
    message = serialize_result([[5, 8]], [[0, 0], [1, 0]], confidence_percent)
    parsed, conf = parse_serialized_message(message)

    assert parsed[0] == [[5, 8]]
    assert parsed[1] == [[0, 0], [1, 0]]
    assert conf == "875"


def test_pi_to_esp32_serial_frame_round_trip() -> None:
    message = serialize_result([[5, 8]], [[0, 0], [1, 0]], 95.2)
    framed = frame_serial_message(message)
    assert unframe_serial_message(framed) == message
    assert framed.startswith("PI2ESP|")
