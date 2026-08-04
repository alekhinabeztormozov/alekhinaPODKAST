from __future__ import annotations

import argparse
import logging
import subprocess
import sys
from pathlib import Path

from media.ambient import AMBIENT_DIR, AMBIENTS, DURATION, AmbientTrack

log = logging.getLogger("audio.ambient")


def _filter_complex(track: AmbientTrack, input_count: int) -> str:
    labels = "".join(f"[{i}]" for i in range(input_count))
    chain = [f"{labels}amix=inputs={input_count}:normalize=0", f"volume={track.volume}"]
    if track.tremolo > 0:
        chain.append(f"tremolo=f={track.tremolo}:d=0.3")
    chain.append(f"lowpass=f={track.lowpass}")
    if track.echo:
        chain.append("aecho=0.8:0.7:80:0.3")
    chain.append("aformat=sample_rates=44100:channel_layouts=stereo")
    return ",".join(chain)


def _build_command(track: AmbientTrack, ffmpeg: str) -> list[str]:
    cmd = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error"]
    for frequency in track.frequencies:
        cmd += ["-f", "lavfi", "-i", f"sine=frequency={frequency}:duration={DURATION}"]
    input_count = len(track.frequencies)
    if track.noise:
        cmd += ["-f", "lavfi", "-i", f"anoisesrc=color=brown:duration={DURATION}:amplitude=0.3"]
        input_count += 1
    cmd += ["-filter_complex", _filter_complex(track, input_count)]
    cmd += ["-ac", "2", "-ar", "44100", "-b:a", "128k", str(track.path)]
    return cmd


def generate(ffmpeg: str = "ffmpeg") -> list[Path]:
    AMBIENT_DIR.mkdir(parents=True, exist_ok=True)
    created: list[Path] = []
    for track in AMBIENTS:
        result = subprocess.run(_build_command(track, ffmpeg), capture_output=True, text=True)
        if result.returncode != 0:
            tail = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else ""
            raise RuntimeError(f"ffmpeg упал на {track.id}: {tail}")
        created.append(track.path)
        log.info("собран эмбиент %s -> %s", track.id, track.path.name)
    return created


def _cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Генератор фоновых эмбиентов.")
    parser.add_argument("--ffmpeg", default="ffmpeg")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    created = generate(args.ffmpeg)
    log.info("готово: %d треков", len(created))
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
