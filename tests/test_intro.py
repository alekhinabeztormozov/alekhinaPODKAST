from __future__ import annotations

from media import intro


def test_intro_present_and_supported():
    path = intro.get_intro()
    assert path is not None, "заставка не найдена в media/assets/intro/"
    assert path.is_file()
    assert path.suffix.lower() in intro.SUPPORTED


def test_intro_none_when_dir_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(intro, "INTRO_DIR", tmp_path / "nope")
    assert intro.get_intro() is None


def test_intro_none_when_dir_empty(tmp_path, monkeypatch):
    empty = tmp_path / "intro"
    empty.mkdir()
    monkeypatch.setattr(intro, "INTRO_DIR", empty)
    assert intro.get_intro() is None
