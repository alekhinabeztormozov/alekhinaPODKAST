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

SILENCE_END_TOLERANCE = 0.1


@dataclass(frozen=True)
class AudioProfile:
    loudness_i: float = -16.0
    loudness_tp: float = -1.5
    loudness_lra: float = 11.0
    music_volume: float = 0.04
    duck_threshold: float = 0.03
    duck_ratio: float = 8.0
    duck_attack: int = 20
    duck_release: int = 1200
    music_fade: float = 2.0
    jingle_loudness_i: float = -18.0
    jingle_open_seconds: float = 12.0
    jingle_close_seconds: float = 15.0
    jingle_fade_in: float = 1.0
    jingle_fade_out: float = 3.0
    silence_threshold_db: float = -50.0
    bitrate: str = "192k"
    sample_rate: int = 44100
    channels: int = 2
    voice_cleanup: str = (
        "highpass=f=80,"
        "afftdn=nr=10:nf=-40,"
        "equalizer=f=250:t=q:w=1.2:g=-2,"
        "equalizer=f=3500:t=q:w=1.0:g=2,"
        "acompressor=threshold=-24dB:ratio=3:attack=15:release=250:makeup=4"
    )


@dataclass
class PipelineInputs:
    voice: Path
    intro: Path | None = None
    outro: Path | None = None
    music: Path | None = None
    jingle: Path | None = None
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


def probe_sound_end(
    path: Path, threshold_db: float, ffmpeg: str = "ffmpeg", ffprobe: str = "ffprobe",
) -> float:
    duration = probe_duration(path, ffprobe)
    result = subprocess.run(
        [_resolve_bin("ffmpeg", ffmpeg), "-hide_banner", "-nostdin", "-i", str(path),
         "-af", f"silencedetect=n={threshold_db}dB:d=0.5", "-f", "null", "-"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    last_silence_start: float | None = None
    last_silence_end: float | None = None
    for line in result.stderr.splitlines():
        if "silence_start:" in line:
            last_silence_start = float(line.split("silence_start:")[1].split()[0])
            last_silence_end = None
        elif "silence_end:" in line:
            last_silence_end = float(line.split("silence_end:")[1].split()[0])
    if last_silence_start is None:
        return duration
    reaches_file_end = last_silence_end is None or last_silence_end >= duration - SILENCE_END_TOLERANCE
    return last_silence_start if reaches_file_end else duration


def _input_order(inp: PipelineInputs) -> list[str]:
    candidates = (
        ("intro", inp.intro), ("voice", inp.voice), ("music", inp.music),
        ("jingle", inp.jingle), ("outro", inp.outro),
    )
    return [name for name, path in candidates if path]


def _jingle_parts(profile: AudioProfile, jingle_end: float | None) -> list[str]:
    opener_fade_start = max(0.0, profile.jingle_open_seconds - profile.jingle_fade_out)
    end = jingle_end if jingle_end is not None else profile.jingle_close_seconds
    closer_start = max(0.0, end - profile.jingle_close_seconds)
    closer_fade_start = max(0.0, end - closer_start - profile.jingle_fade_in)
    return [
        "[jinglef]asplit=2[jopenraw][jcloseraw]",
        f"[jopenraw]atrim=0:{profile.jingle_open_seconds},"
        f"afade=t=out:st={opener_fade_start:.3f}:d={profile.jingle_fade_out}[jopen]",
        f"[jcloseraw]atrim={closer_start:.3f}:{end:.3f},asetpts=PTS-STARTPTS,"
        f"afade=t=in:d={profile.jingle_fade_in},"
        f"afade=t=out:st={closer_fade_start:.3f}:d={profile.jingle_fade_in}[jclose]",
    ]


def _loudnorm(profile: AudioProfile, segment: str) -> str:
    target = profile.jingle_loudness_i if segment in ("jopen", "jclose") else profile.loudness_i
    return f"loudnorm=I={target}:TP={profile.loudness_tp}:LRA={profile.loudness_lra}"


def build_filter_complex(
    inp: PipelineInputs,
    voice_duration: float | None = None,
    jingle_end: float | None = None,
) -> tuple[str, str]:
    profile = inp.profile
    order = _input_order(inp)
    index = {name: i for i, name in enumerate(order)}

    parts: list[str] = []
    fmt = f"aformat=sample_rates={profile.sample_rate}:channel_layouts=stereo"
    for name in order:
        chain = f"{fmt},{profile.voice_cleanup}" if name == "voice" and profile.voice_cleanup else fmt
        parts.append(f"[{index[name]}:a]{chain}[{name}f]")

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

    if inp.jingle:
        parts.extend(_jingle_parts(profile, jingle_end))

    segments: list[str] = []
    if inp.intro:
        segments.append("introf")
    if inp.jingle:
        segments.append("jopen")
    segments.append("body")
    if inp.jingle:
        segments.append("jclose")
    if inp.outro:
        segments.append("outrof")

    if len(segments) == 1:
        parts.append(f"[body]{_loudnorm(profile, 'body')}[out]")
        return ";".join(parts), "[out]"

    for segment in segments:
        parts.append(f"[{segment}]{_loudnorm(profile, segment)}[{segment}n]")
    joined = "".join(f"[{segment}n]" for segment in segments)
    parts.append(f"{joined}concat=n={len(segments)}:v=0:a=1[cat]")
    parts.append(f"[cat]alimiter=limit={10 ** (profile.loudness_tp / 20):.3f}:level=disabled[out]")
    return ";".join(parts), "[out]"


def _ordered_inputs(inp: PipelineInputs) -> list[tuple[list[str], Path]]:
    paths = {
        "intro": inp.intro, "voice": inp.voice, "music": inp.music,
        "jingle": inp.jingle, "outro": inp.outro,
    }
    return [
        (["-stream_loop", "-1"] if name == "music" else [], paths[name])
        for name in _input_order(inp)
    ]


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
        ("outro", inp.outro), ("music", inp.music), ("jingle", inp.jingle),
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
    jingle_end: float | None = None
    if inp.jingle:
        jingle_end = probe_sound_end(inp.jingle, inp.profile.silence_threshold_db, ffmpeg, ffprobe)
    filter_complex, out_label = build_filter_complex(inp, voice_duration, jingle_end)
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
    parser.add_argument("--jingle", type=Path)
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
        music=args.music, jingle=args.jingle, profile=profile,
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
