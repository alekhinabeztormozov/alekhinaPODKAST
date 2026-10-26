from __future__ import annotations

import subprocess
from pathlib import Path

from config import BASE_DIR, get_settings

WIDTH = 1080
HEIGHT = 1920
FPS = 30
FONTS_DIR = BASE_DIR / "pdf" / "fonts"
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
SONG_FADE = 0.8
SOCIAL_LOUDNESS = "loudnorm=I=-14:TP=-1.5:LRA=11"
SFX_VOLUME = 0.6
ENCODE = [
    "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-movflags", "+faststart",
]


class RenderError(RuntimeError):
    pass


def _cover_filter() -> str:
    return (
        f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
        f"crop={WIDTH}:{HEIGHT},setsar=1,fps={FPS}"
    )


def _subtitles_filter(ass_name: str) -> str:
    fonts = FONTS_DIR.as_posix().replace(":", "\\:")
    return f"subtitles={ass_name}:fontsdir='{fonts}'"


def _run(cmd: list[str], work_dir: Path) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=work_dir)
    if result.returncode != 0:
        tail = "\n".join(result.stderr.strip().splitlines()[-4:])
        raise RenderError(f"ffmpeg упал (код {result.returncode}): {tail}")


def _write_ass(ass_text: str, out_path: Path) -> Path:
    ass_path = out_path.with_suffix(".ass")
    ass_path.write_text(ass_text, encoding="utf-8")
    return ass_path


def avatar_audio_chain(offsets: list[float]) -> str:
    if not offsets:
        return f"[0:a]{SOCIAL_LOUDNESS}[a]"
    parts = []
    for number, offset in enumerate(offsets, start=1):
        delay = int(offset * 1000)
        parts.append(f"[{number}:a]adelay={delay}|{delay},volume={SFX_VOLUME}[sfx{number}]")
    mixed = "".join(f"[sfx{number}]" for number in range(1, len(offsets) + 1))
    parts.append(
        f"[0:a]{mixed}amix=inputs={len(offsets) + 1}:duration=first:normalize=0,{SOCIAL_LOUDNESS}[a]"
    )
    return ";".join(parts)


def compose_avatar_reel(
    video: Path, ass_text: str, out_path: Path, sounds: list[tuple[Path, float]] | None = None
) -> Path:
    sounds = sounds or []
    out_path.parent.mkdir(parents=True, exist_ok=True)
    ass_path = _write_ass(ass_text, out_path)
    video_chain = f"[0:v]{_cover_filter()},{_subtitles_filter(ass_path.name)}[v]"
    sound_inputs = [arg for sound, _ in sounds for arg in ("-i", str(sound.resolve()))]
    audio_chain = avatar_audio_chain([offset for _, offset in sounds])
    cmd = [
        get_settings().ffmpeg_bin, "-hide_banner", "-nostdin", "-y", "-i", str(video.resolve()), *sound_inputs,
        "-filter_complex", f"{video_chain};{audio_chain}",
        "-map", "[v]", "-map", "[a]", *ENCODE, out_path.name,
    ]
    try:
        _run(cmd, out_path.parent)
    finally:
        ass_path.unlink(missing_ok=True)
    return out_path


def _visual_input(visual: Path, length: float) -> list[str]:
    if visual.suffix.lower() in IMAGE_SUFFIXES:
        return ["-loop", "1", "-framerate", str(FPS), "-t", f"{length:.2f}", "-i", str(visual.resolve())]
    return ["-stream_loop", "-1", "-t", f"{length:.2f}", "-i", str(visual.resolve())]


def _song_video_chain(visual: Path, length: float, ass_name: str) -> str:
    frames = int(length * FPS)
    if visual.suffix.lower() in IMAGE_SUFFIXES:
        motion = (
            f"scale={WIDTH * 2}:{HEIGHT * 2}:force_original_aspect_ratio=increase,"
            f"crop={WIDTH * 2}:{HEIGHT * 2},"
            f"zoompan=z='min(1+0.0009*on,1.25)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            f":d={frames}:s={WIDTH}x{HEIGHT}:fps={FPS},setsar=1"
        )
    else:
        motion = _cover_filter()
    return f"[0:v]{motion},{_subtitles_filter(ass_name)},trim=duration={length:.2f}[v]"


def compose_song_reel(
    track: Path, visual: Path, ass_text: str, out_path: Path, start: float, length: float
) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    ass_path = _write_ass(ass_text, out_path)
    fade_out = max(0.0, length - SONG_FADE)
    audio_chain = (
        f"[1:a]atrim=start={start:.2f}:duration={length:.2f},asetpts=PTS-STARTPTS,"
        f"afade=t=in:d={SONG_FADE},afade=t=out:st={fade_out:.2f}:d={SONG_FADE},{SOCIAL_LOUDNESS}[a]"
    )
    cmd = [
        get_settings().ffmpeg_bin, "-hide_banner", "-nostdin", "-y",
        *_visual_input(visual, length), "-i", str(track.resolve()),
        "-filter_complex", f"{_song_video_chain(visual, length, ass_path.name)};{audio_chain}",
        "-map", "[v]", "-map", "[a]", "-t", f"{length:.2f}", *ENCODE, out_path.name,
    ]
    try:
        _run(cmd, out_path.parent)
    finally:
        ass_path.unlink(missing_ok=True)
    return out_path


def loudness_per_second(track: Path) -> list[float]:
    cmd = [
        get_settings().ffmpeg_bin, "-hide_banner", "-nostdin", "-i", str(track.resolve()),
        "-af", "aresample=8000,asetnsamples=n=8000,astats=metadata=1:reset=1,"
               "ametadata=print:key=lavfi.astats.Overall.RMS_level:file=-",
        "-f", "null", "-",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    levels = []
    for line in result.stdout.splitlines():
        if "RMS_level=" in line:
            value = line.split("=", 1)[1].strip()
            levels.append(float(value) if value not in ("-inf", "inf", "nan") else -90.0)
    return levels


def loudest_start(levels: list[float], length: int) -> float:
    if len(levels) <= length:
        return 0.0
    window = sum(levels[:length])
    best_sum, best_start = window, 0
    for start in range(1, len(levels) - length + 1):
        window += levels[start + length - 1] - levels[start - 1]
        if window > best_sum:
            best_sum, best_start = window, start
    return float(best_start)


def cut_audio(track: Path, start: float, length: float, out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        get_settings().ffmpeg_bin, "-hide_banner", "-nostdin", "-y",
        "-ss", f"{start:.2f}", "-t", f"{length:.2f}", "-i", str(track.resolve()),
        "-vn", "-c:a", "libmp3lame", "-b:a", "128k", out_path.name,
    ]
    _run(cmd, out_path.parent)
    return out_path
