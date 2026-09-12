from __future__ import annotations

from types import SimpleNamespace

import numpy as np

from ras_final.models.model1_stitching.stitch import Stitcher
from ras_final.pipeline import SARPiPipeline
from ras_final.payload import build_compact_payload, format_confidence, parse_compact_payload


def test_normalized_confidence_is_converted_before_integer_formatting() -> None:
    assert format_confidence(0.875) == "087"


def test_payload_uses_the_documented_json_schema() -> None:
    payload = build_compact_payload([[5, 8]], [[0, 0], [1, 0]])
    assert payload == '{"v":[[5,8]],"p":[[0,0],[1,0]]}'
    assert parse_compact_payload(payload) == {"v": [[5, 8]], "p": [[0, 0], [1, 0]]}


def test_detect_and_plan_targets_a_mapped_victim_cell() -> None:
    pipeline = SARPiPipeline.__new__(SARPiPipeline)
    pipeline.detector = SimpleNamespace(predict=lambda _: [
        SimpleNamespace(class_name="victim", confidence=0.9, x1=12.0, x2=20.0, y1=8.0, y2=16.0, bbox=[12, 8, 20, 16])
    ])

    result = pipeline.detect_and_plan(np.zeros((32, 32, 3), dtype=np.uint8))

    assert result.path[-1] == result.persons[0]
    assert parse_compact_payload(result.payload)["v"] == result.persons


def test_stitch_failure_returns_latest_frame() -> None:
    stitcher = Stitcher()
    latest = np.full((2, 2, 3), 7, dtype=np.uint8)
    stitcher._stitcher = SimpleNamespace(stitch=lambda _: (1, None))

    assert np.array_equal(stitcher([np.zeros((2, 2, 3), dtype=np.uint8), latest]), latest)
