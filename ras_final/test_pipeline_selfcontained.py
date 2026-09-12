from __future__ import annotations

import pathlib


def test_ras_final_has_no_external_model_or_comms_imports() -> None:
    root = pathlib.Path(__file__).resolve().parent
    for path in sorted(root.rglob("*.py")):
        if path.name == "test_pipeline_selfcontained.py":
            continue
        text = path.read_text(encoding="utf-8")
        assert "from models" not in text
        assert "import models" not in text
        assert "from comms" not in text
        assert "import comms" not in text


def test_pipeline_uses_local_package_paths_only() -> None:
    import ras_final.pipeline as pipeline_mod

    assert str(pathlib.Path(pipeline_mod.__file__).resolve()).startswith(str(pathlib.Path(__file__).resolve().parent))
