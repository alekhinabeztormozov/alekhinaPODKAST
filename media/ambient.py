from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

AMBIENT_DIR = Path(__file__).resolve().parent / "assets" / "ambient"
DURATION = 60


@dataclass(frozen=True)
class AmbientTrack:
    id: str
    title: str
    description: str
    frequencies: list[float]
    volume: float = 0.28
    lowpass: int = 1200
    tremolo: float = 0.0
    echo: bool = True
    noise: bool = False
    extra: list[str] = field(default_factory=list)

    @property
    def filename(self) -> str:
        return f"{self.id}.mp3"

    @property
    def path(self) -> Path:
        return AMBIENT_DIR / self.filename


AMBIENTS: list[AmbientTrack] = [
    AmbientTrack(
        id="neutral",
        title="Нейтральный",
        description="Спокойный ровный фон, ни к чему не тянет.",
        frequencies=[130.81, 196.00, 261.63],
        volume=0.26,
        lowpass=1400,
        tremolo=0.18,
    ),
    AmbientTrack(
        id="warm",
        title="Тёплый",
        description="Мягкий низкий пэд, уютно и обволакивающе.",
        frequencies=[98.00, 146.83, 196.00],
        volume=0.30,
        lowpass=1000,
        tremolo=0.12,
    ),
    AmbientTrack(
        id="minimal",
        title="Минимал",
        description="Едва слышный дрон, почти тишина.",
        frequencies=[110.00, 220.00],
        volume=0.20,
        lowpass=900,
        tremolo=0.0,
        echo=False,
    ),
    AmbientTrack(
        id="cinematic",
        title="Кинематограф",
        description="Широкий минорный аккорд с воздухом, для драматичных разборов.",
        frequencies=[110.00, 130.81, 164.81],
        volume=0.30,
        lowpass=1600,
        tremolo=0.10,
    ),
    AmbientTrack(
        id="lofi",
        title="Лоу-фай",
        description="Тёплый шум и глухой пэд, ламповое звучание.",
        frequencies=[87.31, 130.81, 174.61],
        volume=0.24,
        lowpass=800,
        tremolo=0.20,
        noise=True,
    ),
]


def find_ambient(ambient_id: str) -> AmbientTrack | None:
    return next((track for track in AMBIENTS if track.id == ambient_id), None)
