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


@dataclass(frozen=True)
class AudioProfile:
    loudness_i: float = -16.0
    loudness_tp: float = -1.5
    loudness_lra: float = 11.0
    music_volume: float = 0.18
    duck_threshold: float = 0.03
    duck_ratio: float = 8.0
    duck_attack: int = 20
    duck_release: int = 350
    music_fade: float = 2.0
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
    candidate = override or name
    found = shutil.which(candidate)
    if not found:
        raise PipelineError(
            f"{name} не найден (искал '{candidate}'). Установи ffmpeg "
            f"или задай путь через --ffmpeg/--ffprobe."
        )
    return found


def probe_duration(path: Path, ffprobe: str = "ffprobe") -> float:
    exe = _resolve_bin("ffprobe", ffprobe)
    result = subprocess.run(
        [exe, "-v", "error", "-show_entries", "format=duration",
         "-of", "json", str(path)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if result.returncode != 0:
        raise PipelineError(f"ffprobe упал на {path}: {result.stderr.strip()}")
    try:
        return float(json.loads(result.stdout)["format"]["duration"])
    except (KeyError, ValueError, json.JSONDecodeError) as exc:
        raise PipelineError(f"не разобрал длительность {path}: {exc}") from exc


def build_filter_complex(inp: PipelineInputs, voice_duration: float | None = None) -> tuple[str, str]:
    profile = inp.profile
    order: list[str] = []
    if inp.intro:
        order.append("intro")
    order.append("voice")
    if inp.music:
        order.append("music")
    if inp.outro:
        order.append("outro")
    index = {name: i for i, name in enumerate(order)}

    parts: list[str] = []
    fmt = f"aformat=sample_rates={profile.sample_rate}:channel_layouts=stereo"
    for name in order:
        parts.append(f"[{index[name]}:a]{fmt}[{name}f]")

    if inp.music:
        parts.append("[voicef]asplit=2[vmain][vside]")
        parts.append(
            f"[musicf]volume={profile.music_volume},afade=t=in:d={profile.music_fade}[bgraw]"
        )
        parts.append(
            f"[bgraw][vside]sidechaincompress="
            f"threshold={profile.duck_threshold}:ratio={profile.duck_ratio}:"
            f"attack={profile.duck_attack}:release={profile.duck_release}[bgduck]"
        )
        duck_out = "[bgduck]"
        if voice_duration is not None:
            fade_start = max(0.0, voice_duration - profile.music_fade)
            parts.append(f"[bgduck]afade=t=out:st={fade_start:.3f}:d={profile.music_fade}[bgfade]")
            duck_out = "[bgfade]"
        parts.append(
            f"[vmain]{duck_out}amix=inputs=2:duration=first:normalize=0[body]"
        )
    else:
        parts.append("[voicef]anull[body]")

    segments: list[str] = []
    if inp.intro:
        segments.append("[introf]")
    segments.append("[body]")
    if inp.outro:
        segments.append("[outrof]")

    if len(segments) > 1:
        n = len(segments)
        parts.append(f"{''.join(segments)}concat=n={n}:v=0:a=1[cat]")
        stitched = "[cat]"
    else:
        stitched = "[body]"

    parts.append(
        f"{stitched}loudnorm=I={profile.loudness_i}:"
        f"TP={profile.loudness_tp}:LRA={profile.loudness_lra}[out]"
    )
    return ";".join(parts), "[out]"


def _ordered_inputs(inp: PipelineInputs) -> list[tuple[list[str], Path]]:
    items: list[tuple[list[str], Path]] = []
    if inp.intro:
        items.append(([], inp.intro))
    items.append(([], inp.voice))
    if inp.music:
        items.append((["-stream_loop", "-1"], inp.music))
    if inp.outro:
        items.append(([], inp.outro))
    return items


def process_episode(
    inp: PipelineInputs,
    out_path: Path,
    ffmpeg: str = "ffmpeg",
    ffprobe: str = "ffprobe",
    overwrite: bool = True,
) -> Path:
    ffmpeg_exe = _resolve_bin("ffmpeg", ffmpeg)
    _resolve_bin("ffprobe", ffprobe)

    for label, path in (
        ("voice", inp.voice), ("intro", inp.intro),
        ("outro", inp.outro), ("music", inp.music),
    ):
        if path and not path.exists():
            raise PipelineError(f"{label}: файл не найден — {path}")

    out_path.parent.mkdir(parents=True, exist_ok=True)

    voice_duration: float | None = None
    if inp.music:
        try:
            voice_duration = probe_duration(inp.voice, ffprobe)
        except PipelineError:
            log.warning("не измерил длину голоса — финальный фейд музыки пропущен")
    filter_complex, out_label = build_filter_complex(inp, voice_duration)
    inputs = _ordered_inputs(inp)
    cmd: list[str] = [ffmpeg_exe, "-hide_banner", "-nostdin"]
    cmd += ["-y"] if overwrite else ["-n"]
    for opts, path in inputs:
        cmd += [*opts, "-i", str(path)]
    cmd += ["-filter_complex", filter_complex, "-map", out_label]
    cmd += [
        "-c:a", "libmp3lame", "-b:a", inp.profile.bitrate,
        "-ar", str(inp.profile.sample_rate), "-ac", str(inp.profile.channels),
        str(out_path),
    ]

    log.info("ffmpeg run: %d inputs -> %s", len(inputs), out_path)
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        tail = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else ""
        raise PipelineError(f"ffmpeg упал (код {result.returncode}): {tail}")

    if not out_path.exists() or out_path.stat().st_size == 0:
        raise PipelineError(f"выход пустой: {out_path}")
    return out_path


def _cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="ffmpeg-пайплайн эпизода подкаста «Алёхина без тормозов».",
    )
    parser.add_argument("--voice", required=True, type=Path)
    parser.add_argument("--intro", type=Path)
    parser.add_argument("--outro", type=Path)
    parser.add_argument("--music", type=Path)
    parser.add_argument("-o", "--out", required=True, type=Path)
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--ffprobe", default="ffprobe")
    parser.add_argument("--music-volume", type=float)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    profile = AudioProfile(music_volume=args.music_volume) if args.music_volume is not None else AudioProfile()
    inp = PipelineInputs(
        voice=args.voice, intro=args.intro, outro=args.outro,
        music=args.music, profile=profile,
    )
    try:
        out = process_episode(inp, args.out, ffmpeg=args.ffmpeg, ffprobe=args.ffprobe)
    except PipelineError as exc:
        log.error("%s", exc)
        return 1
    duration = probe_duration(out, args.ffprobe)
    log.info("готово: %s (%.1f сек, %.2f МБ)", out, duration, out.stat().st_size / 1e6)
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
