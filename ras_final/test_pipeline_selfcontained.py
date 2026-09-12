from __future__ import annotations

import pathlib


def test_runtime_uses_package_relative_imports() -> None:
    root = pathlib.Path(__file__).resolve().parent
    for path in sorted(root.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        assert "from payload import" not in text
        assert "from lora_sender import" not in text


def test_weights_directory_placeholder_is_tracked() -> None:
    assert (pathlib.Path(__file__).resolve().parent / "weights" / ".gitkeep").is_file()
