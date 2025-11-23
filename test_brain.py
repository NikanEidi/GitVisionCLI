from pathlib import Path

from gitvisioncli.core.brain import Brain


def test_brain_remember_get_forget_isolated_by_project(tmp_path, monkeypatch):
    base_a = tmp_path / "projA"
    base_b = tmp_path / "projB"
    base_a.mkdir()
    base_b.mkdir()

    storage = tmp_path / ".gv"

    brain_a = Brain(base_dir=base_a, storage_dir=storage)
    brain_b = Brain(base_dir=base_b, storage_dir=storage)

    brain_a.remember("theme", "neon")
    assert brain_a.get("theme") == "neon"
    # Other project must not see this value
    assert brain_b.get("theme") is None

    brain_a.forget("theme")
    assert brain_a.get("theme") is None

