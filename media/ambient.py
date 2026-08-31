from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

AMBIENT_DIR = Path(__file__).resolve().parent / "assets" / "ambient"
SUPPORTED = (".mp3", ".wav", ".ogg", ".m4a", ".flac")

KNOWN_META: dict[str, tuple[str, str]] = {
    "drifting-dreams": ("Плывущие грёзы", "Мягкий воздушный эмбиент, мечтательный фон."),
    "gentle-breeze": ("Лёгкий бриз", "Прозрачный спокойный пэд."),
    "lullaby-of-tranquility": ("Колыбельная", "Убаюкивающий тёплый фон."),
    "serene-reverie": ("Безмятежность", "Светлый умиротворённый эмбиент."),
    "serenity-by-the-stream": ("У ручья", "Спокойный тягучий фон."),
    "jaga-instrumental": ("JAGA (авторский)", "Авторский инструментал от клиента, ритмичный фон."),
}


@dataclass(frozen=True)
class AmbientTrack:
    id: str
    title: str
    description: str
    path: Path

    @property
    def filename(self) -> str:
        return self.path.name

    @property
    def code(self) -> str:
        """Короткий ASCII-ключ для callback_data (у Telegram лимит 64 байта)."""
        return _code(self.id)


def _code(stem: str) -> str:
    raw = stem.encode()
    if stem.isascii() and len(raw) <= 48:
        return stem
    return "h" + hashlib.sha1(raw).hexdigest()[:16]


def _humanize(stem: str) -> str:
    cleaned = re.sub(r"[_-]?\d+$", "", stem)
    cleaned = cleaned.replace("_", " ").replace("-", " ").strip()
    return cleaned.capitalize() or stem


def get_ambients() -> list[AmbientTrack]:
    if not AMBIENT_DIR.is_dir():
        return []
    tracks: list[AmbientTrack] = []
    for path in AMBIENT_DIR.iterdir():
        if not path.is_file() or path.suffix.lower() not in SUPPORTED:
            continue
        title, description = KNOWN_META.get(path.stem, (_humanize(path.stem), ""))
        tracks.append(AmbientTrack(id=path.stem, title=title, description=description, path=path))
    order = {key: index for index, key in enumerate(KNOWN_META)}
    tracks.sort(key=lambda track: (order.get(track.id, len(order)), track.title.lower()))
    return tracks


def find_ambient(ambient_id: str) -> AmbientTrack | None:
    """Ищет по id (имя файла) или по короткому коду из callback_data."""
    return next(
        (t for t in get_ambients() if ambient_id in (t.id, t.code)),
        None,
    )
