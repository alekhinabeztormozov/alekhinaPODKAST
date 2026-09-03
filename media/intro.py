from __future__ import annotations

from pathlib import Path

INTRO_DIR = Path(__file__).resolve().parent / "assets" / "intro"
SUPPORTED = (".mp3", ".wav", ".ogg", ".m4a", ".flac")


def get_intro() -> Path | None:
    """Заставка, которая приклеивается в начало каждого эпизода.

    Первый подходящий аудиофайл из ``media/assets/intro/``. Владелец меняет
    заставку, просто положив новый файл в папку (как с эмбиентами).
    """
    if not INTRO_DIR.is_dir():
        return None
    for path in sorted(INTRO_DIR.iterdir()):
        if path.is_file() and path.suffix.lower() in SUPPORTED:
            return path
    return None
