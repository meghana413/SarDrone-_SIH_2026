from __future__ import annotations

from ras_final.protocol import chunk_message, frame_serial_message, parse_serialized_message, reconstruct_message, serialize_result, unframe_serial_message


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
