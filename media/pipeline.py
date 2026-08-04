"""ffmpeg аудио-пайплайн основного подкаста (PROJECT.md р.4.2, первый шаг р.12).

Схема:  интро + [ голос  микс  музыка-подложка(ducking) ] + аутро  ->  loudnorm  ->  mp3

БЕЗ нейронки — детерминированный ffmpeg, ноль затрат на токены.
Ассеты (интро/аутро/заставка/музыка) даёт клиент; аудиобонусы и голосовые
разборы для закрытого канала НЕ обрабатываются (сырые записи).

Модуль stdlib-only — запускается без установки бот-зависимостей:

    python -m media.pipeline --voice raw.mp3 --intro intro.mp3 \
        --music bg.mp3 --outro outro.mp3 -o media/out/ep01.mp3

Минимально нужен только --voice. Остальное опционально.
"""
from __future__ import annotations

import argparse
import json
import logging
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

log = logging.getLogger("audio.pipeline")


# --- параметры звука (можно тюнить под вкус клиента) ---
@dataclass(frozen=True)
class AudioProfile:
    # EBU R128 нормализация громкости под подкаст-площадки
    loudness_i: float = -16.0        # целевая интегральная громкость, LUFS
    loudness_tp: float = -1.5        # true peak, dBTP
    loudness_lra: float = 11.0       # loudness range
    # музыка-подложка
    music_volume: float = 0.18       # 0..1, громкость подложки до ducking
    duck_threshold: float = 0.03     # порог ducking (голос давит музыку)
    duck_ratio: float = 8.0
    duck_attack: int = 20            # мс
    duck_release: int = 350          # мс
    music_fade: float = 2.0          # сек фейд-ин/аут подложки
    # выход
    bitrate: str = "192k"
    sample_rate: int = 44100
    channels: int = 2


@dataclass
class PipelineInputs:
    voice: Path
    intro: Path | None = None
    outro: Path | None = None
    music: Path | None = None
    profile: AudioProfile = field(default_factory=AudioProfile)


class PipelineError(RuntimeError):
    pass


def _resolve_bin(name: str, override: str | None) -> str:
    cand = override or name
    found = shutil.which(cand)
    if not found:
        raise PipelineError(
            f"{name} не найден (искал '{cand}'). Установи ffmpeg или задай путь "
            f"через --ffmpeg/--ffprobe."
        )
    return found


def probe_duration(path: Path, ffprobe: str = "ffprobe") -> float:
    """Длительность аудио в секундах через ffprobe."""
    exe = _resolve_bin("ffprobe", ffprobe)
    out = subprocess.run(
        [exe, "-v", "error", "-show_entries", "format=duration",
         "-of", "json", str(path)],
        capture_output=True, text=True,
    )
    if out.returncode != 0:
        raise PipelineError(f"ffprobe упал на {path}: {out.stderr.strip()}")
    try:
        return float(json.loads(out.stdout)["format"]["duration"])
    except (KeyError, ValueError, json.JSONDecodeError) as e:
        raise PipelineError(f"не разобрал длительность {path}: {e}") from e


def build_filter_complex(inp: PipelineInputs) -> tuple[list[str], str]:
    """Строит filter_complex и метку выходного стрима.

    Индексы входов ffmpeg назначаются в порядке: intro, voice, music, outro
    (только присутствующие). Возвращает (аргументы -i в этом же порядке заранее
    считаны вызывающим кодом, здесь — только фильтр).
    """
    p = inp.profile
    # карта: имя -> индекс входа в порядке добавления
    order: list[str] = []
    if inp.intro:
        order.append("intro")
    order.append("voice")
    if inp.music:
        order.append("music")
    if inp.outro:
        order.append("outro")
    idx = {name: i for i, name in enumerate(order)}

    parts: list[str] = []

    # нормализуем формат каждого входа к общему (иначе concat/amix ругаются)
    fmt = f"aformat=sample_rates={p.sample_rate}:channel_layouts=stereo"
    for name in order:
        parts.append(f"[{idx[name]}:a]{fmt}[{name}f]")

    # тело: голос (+ подложка с ducking)
    if inp.music:
        # голос нужен дважды (как основа микса и как sidechain) — расщепляем,
        # иначе ffmpeg переиспользует один лейбл и режет длительность
        parts.append("[voicef]asplit=2[vmain][vside]")
        # музыка луп на всю длину голоса, тише, с фейд-ином
        parts.append(
            f"[musicf]aloop=loop=-1:size=2147483647,volume={p.music_volume},"
            f"afade=t=in:d={p.music_fade}[bgraw]"
        )
        # sidechaincompress: [main=music][side=voice] -> ducked music
        parts.append(
            f"[bgraw][vside]sidechaincompress="
            f"threshold={p.duck_threshold}:ratio={p.duck_ratio}:"
            f"attack={p.duck_attack}:release={p.duck_release}[bgduck]"
        )
        parts.append(
            "[vmain][bgduck]amix=inputs=2:duration=first:normalize=0[body]"
        )
    else:
        parts.append("[voicef]anull[body]")

    # concat интро + тело + аутро (только присутствующие)
    seg: list[str] = []
    if inp.intro:
        seg.append("[introf]")
    seg.append("[body]")
    if inp.outro:
        seg.append("[outrof]")

    if len(seg) > 1:
        n = len(seg)
        parts.append(f"{''.join(seg)}concat=n={n}:v=0:a=1[cat]")
        cat = "[cat]"
    else:
        cat = "[body]"

    # финальная нормализация громкости под площадки
    parts.append(
        f"{cat}loudnorm=I={p.loudness_i}:TP={p.loudness_tp}:LRA={p.loudness_lra}[out]"
    )
    return [";".join(parts)], "[out]"


def _ordered_input_paths(inp: PipelineInputs) -> list[Path]:
    paths: list[Path] = []
    if inp.intro:
        paths.append(inp.intro)
    paths.append(inp.voice)
    if inp.music:
        paths.append(inp.music)
    if inp.outro:
        paths.append(inp.outro)
    return paths


def process_episode(
    inp: PipelineInputs,
    out_path: Path,
    ffmpeg: str = "ffmpeg",
    ffprobe: str = "ffprobe",
    overwrite: bool = True,
) -> Path:
    """Собирает готовый эпизод. Возвращает путь к результату."""
    ff = _resolve_bin("ffmpeg", ffmpeg)
    _resolve_bin("ffprobe", ffprobe)  # ранняя проверка

    for label, path in (
        ("voice", inp.voice), ("intro", inp.intro),
        ("outro", inp.outro), ("music", inp.music),
    ):
        if path and not path.exists():
            raise PipelineError(f"{label}: файл не найден — {path}")

    out_path.parent.mkdir(parents=True, exist_ok=True)

    filt, out_label = build_filter_complex(inp)
    cmd: list[str] = [ff, "-hide_banner", "-nostdin"]
    cmd += ["-y"] if overwrite else ["-n"]
    for path in _ordered_input_paths(inp):
        cmd += ["-i", str(path)]
    cmd += ["-filter_complex", filt[0], "-map", out_label]
    cmd += [
        "-c:a", "libmp3lame", "-b:a", inp.profile.bitrate,
        "-ar", str(inp.profile.sample_rate), "-ac", str(inp.profile.channels),
        str(out_path),
    ]

    log.info("ffmpeg: %s", " ".join(cmd))
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        # последняя строка stderr обычно содержит суть
        tail = res.stderr.strip().splitlines()[-1] if res.stderr.strip() else ""
        raise PipelineError(f"ffmpeg упал (код {res.returncode}): {tail}")

    if not out_path.exists() or out_path.stat().st_size == 0:
        raise PipelineError(f"выход пустой: {out_path}")
    return out_path


def _cli(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="ffmpeg-пайплайн эпизода подкаста «Алёхина без тормозов».",
    )
    ap.add_argument("--voice", required=True, type=Path, help="сырой голос (обязательно)")
    ap.add_argument("--intro", type=Path, help="интро/заставка")
    ap.add_argument("--outro", type=Path, help="аутро")
    ap.add_argument("--music", type=Path, help="музыка-подложка")
    ap.add_argument("-o", "--out", required=True, type=Path, help="выходной mp3")
    ap.add_argument("--ffmpeg", default="ffmpeg", help="путь к ffmpeg")
    ap.add_argument("--ffprobe", default="ffprobe", help="путь к ffprobe")
    ap.add_argument("--music-volume", type=float, help="громкость подложки 0..1")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    profile = AudioProfile()
    if args.music_volume is not None:
        profile = AudioProfile(music_volume=args.music_volume)

    inp = PipelineInputs(
        voice=args.voice, intro=args.intro, outro=args.outro,
        music=args.music, profile=profile,
    )
    try:
        out = process_episode(inp, args.out, ffmpeg=args.ffmpeg, ffprobe=args.ffprobe)
    except PipelineError as e:
        log.error("%s", e)
        return 1
    dur = probe_duration(out, args.ffprobe)
    log.info("готово: %s (%.1f сек, %.2f МБ)", out, dur, out.stat().st_size / 1e6)
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
