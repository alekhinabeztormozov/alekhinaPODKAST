from __future__ import annotations

import argparse
import logging
import subprocess
import sys
from dataclasses import dataclass

from media.ambient import AMBIENT_DIR

log = logging.getLogger("audio.ambient")
DURATION = 60


@dataclass(frozen=True)
class SynthSpec:
    id: str
    frequencies: list[float]
    volume: float = 0.26
    lowpass: int = 1200
    tremolo: float = 0.0
    echo: bool = True
    noise: bool = False


SYNTH_SPECS: list[SynthSpec] = [
    SynthSpec("neutral", [130.81, 196.00, 261.63], volume=0.26, lowpass=1400, tremolo=0.18),
    SynthSpec("warm", [98.00, 146.83, 196.00], volume=0.30, lowpass=1000, tremolo=0.12),
    SynthSpec("minimal", [110.00, 220.00], volume=0.20, lowpass=900, echo=False),
    SynthSpec("cinematic", [110.00, 130.81, 164.81], volume=0.30, lowpass=1600, tremolo=0.10),
    SynthSpec("lofi", [87.31, 130.81, 174.61], volume=0.24, lowpass=800, tremolo=0.20, noise=True),
]


def _filter_complex(spec: SynthSpec, input_count: int) -> str:
    labels = "".join(f"[{i}]" for i in range(input_count))
    chain = [f"{labels}amix=inputs={input_count}:normalize=0", f"volume={spec.volume}"]
    if spec.tremolo > 0:
        chain.append(f"tremolo=f={spec.tremolo}:d=0.3")
    chain.append(f"lowpass=f={spec.lowpass}")
    if spec.echo:
        chain.append("aecho=0.8:0.7:80:0.3")
    chain.append("aformat=sample_rates=44100:channel_layouts=stereo")
    return ",".join(chain)


def _build_command(spec: SynthSpec, ffmpeg: str) -> list[str]:
    cmd = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error"]
    for frequency in spec.frequencies:
        cmd += ["-f", "lavfi", "-i", f"sine=frequency={frequency}:duration={DURATION}"]
    input_count = len(spec.frequencies)
    if spec.noise:
        cmd += ["-f", "lavfi", "-i", f"anoisesrc=color=brown:duration={DURATION}:amplitude=0.3"]
        input_count += 1
    cmd += ["-filter_complex", _filter_complex(spec, input_count)]
    cmd += ["-ac", "2", "-ar", "44100", "-b:a", "128k", str(AMBIENT_DIR / f"{spec.id}.mp3")]
    return cmd


def generate(ffmpeg: str = "ffmpeg") -> list[str]:
    AMBIENT_DIR.mkdir(parents=True, exist_ok=True)
    created: list[str] = []
    for spec in SYNTH_SPECS:
        result = subprocess.run(_build_command(spec, ffmpeg), capture_output=True, text=True)
        if result.returncode != 0:
            tail = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else ""
            raise RuntimeError(f"ffmpeg упал на {spec.id}: {tail}")
        created.append(spec.id)
        log.info("собран эмбиент %s", spec.id)
    return created


def _cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Генератор дефолтных фоновых эмбиентов.")
    parser.add_argument("--ffmpeg", default="ffmpeg")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    created = generate(args.ffmpeg)
    log.info("готово: %d треков", len(created))
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
