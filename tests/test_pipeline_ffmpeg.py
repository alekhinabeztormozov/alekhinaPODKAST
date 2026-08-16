from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from media.pipeline import AudioProfile, PipelineInputs, probe_duration, process_episode

pytestmark = pytest.mark.skipif(
    shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None,
    reason="ffmpeg/ffprobe не установлены",
)

FFMPEG = shutil.which("ffmpeg") or "ffmpeg"


def _sine(path: Path, seconds: float, freq: int = 220, gaps: bool = False) -> Path:
    filt = "volume='if(lt(mod(t,4),3),0.6,0)':eval=frame" if gaps else "volume=0.6"
    subprocess.run(
        [FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi",
         "-i", f"sine=frequency={freq}:duration={seconds}", "-af", filt,
         "-ac", "2", "-ar", "44100", str(path)],
        check=True, capture_output=True, encoding="utf-8", errors="replace",
    )
    return path


def _segment_rms(path: Path, start: float, end: float) -> float:
    result = subprocess.run(
        [FFMPEG, "-hide_banner", "-i", str(path), "-af",
         f"atrim={start}:{end},astats=metadata=1", "-f", "null", "-"],
        capture_output=True, encoding="utf-8", errors="replace",
    )
    for line in result.stderr.splitlines():
        if "RMS level dB" in line:
            value = line.split("RMS level dB:")[1].strip()
            return float("-inf") if value == "-inf" else float(value)
    return float("-inf")


def test_voice_only_duration(tmp_path):
    voice = _sine(tmp_path / "v.wav", 5)
    out = process_episode(PipelineInputs(voice=voice), tmp_path / "out.mp3", ffmpeg=FFMPEG)
    assert abs(probe_duration(out) - 5) < 0.6


def test_music_shorter_than_voice_loops(tmp_path):
    voice = _sine(tmp_path / "v.wav", 16)
    music = _sine(tmp_path / "m.wav", 3, freq=330)
    out = process_episode(
        PipelineInputs(voice=voice, music=music), tmp_path / "out.mp3", ffmpeg=FFMPEG
    )
    assert abs(probe_duration(out) - 16) < 0.7
    late = _segment_rms(out, 11.0, 13.0)
    assert late > -45.0


def test_music_longer_than_voice_trims(tmp_path):
    voice = _sine(tmp_path / "v.wav", 4)
    music = _sine(tmp_path / "m.wav", 20, freq=330)
    out = process_episode(
        PipelineInputs(voice=voice, music=music), tmp_path / "out.mp3", ffmpeg=FFMPEG
    )
    assert abs(probe_duration(out) - 4) < 0.7


def test_ducking_lowers_music_under_voice(tmp_path):
    voice = _sine(tmp_path / "v.wav", 16, gaps=True)
    music = _sine(tmp_path / "m.wav", 3, freq=330)
    profile = AudioProfile(loudness_i=-16.0)
    out = process_episode(
        PipelineInputs(voice=voice, music=music, profile=profile),
        tmp_path / "out.mp3", ffmpeg=FFMPEG,
    )
    gap_rms = _segment_rms(out, 3.2, 3.8)
    voiced_rms = _segment_rms(out, 1.0, 2.5)
    assert voiced_rms > gap_rms
