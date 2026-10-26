from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from reels.render import compose_avatar_reel, compose_song_reel, cut_audio, loudness_per_second
from reels.subtitles import Word, build_ass

pytestmark = pytest.mark.skipif(
    shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None,
    reason="ffmpeg/ffprobe не установлены",
)

FFMPEG = shutil.which("ffmpeg") or "ffmpeg"
FFPROBE = shutil.which("ffprobe") or "ffprobe"
WORDS = [Word(0.2, 0.7, "вкус"), Word(0.7, 1.2, "из"), Word(1.2, 2.0, "детства")]


def _make(args: list[str]) -> None:
    subprocess.run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", *args], check=True, capture_output=True)


def _streams(path: Path) -> dict:
    result = subprocess.run(
        [FFPROBE, "-v", "error", "-show_entries", "stream=codec_type,width,height:format=duration", "-of", "json",
         str(path)],
        capture_output=True, text=True, check=True,
    )
    return json.loads(result.stdout)


def _video_size(info: dict) -> tuple[int, int]:
    video = next(stream for stream in info["streams"] if stream["codec_type"] == "video")
    return video["width"], video["height"]


def test_song_reel_is_vertical_with_audio(tmp_path):
    image = tmp_path / "hat.png"
    track = tmp_path / "track.mp3"
    _make(["-f", "lavfi", "-i", "color=c=orange:s=800x800", "-frames:v", "1", str(image)])
    _make(["-f", "lavfi", "-i", "sine=frequency=330:duration=12", str(track)])

    out = compose_song_reel(track, image, build_ass(WORDS, "Килька"), tmp_path / "song.mp4", start=2, length=4)

    info = _streams(out)
    assert _video_size(info) == (1080, 1920)
    assert {stream["codec_type"] for stream in info["streams"]} == {"video", "audio"}
    assert 3.8 <= float(info["format"]["duration"]) <= 4.3
    assert not out.with_suffix(".ass").exists()


def test_avatar_reel_crops_landscape_to_vertical(tmp_path):
    source = tmp_path / "avatar.mp4"
    _make([
        "-f", "lavfi", "-i", "testsrc=size=1280x720:rate=25:duration=3",
        "-f", "lavfi", "-i", "sine=frequency=220:duration=3", "-shortest", str(source),
    ])

    out = compose_avatar_reel(source, build_ass(WORDS, "Хук"), tmp_path / "avatar_out.mp4")

    assert _video_size(_streams(out)) == (1080, 1920)


def test_loudness_and_cut(tmp_path):
    track = tmp_path / "steps.mp3"
    _make(["-f", "lavfi", "-i", "sine=frequency=440:duration=6", "-af",
           "volume='if(gt(t,3),1,0.01)':eval=frame", str(track)])

    levels = loudness_per_second(track)
    assert len(levels) >= 5
    assert levels[4] > levels[1] + 20

    clip = cut_audio(track, 3, 2, tmp_path / "clip.mp3")
    assert 1.8 <= float(_streams(clip)["format"]["duration"]) <= 2.2


def test_avatar_reel_mixes_sound_effect(tmp_path):
    source = tmp_path / "avatar.mp4"
    ding = tmp_path / "ding.mp3"
    _make([
        "-f", "lavfi", "-i", "testsrc=size=720x1280:rate=25:duration=3",
        "-f", "lavfi", "-i", "sine=frequency=220:duration=3", "-shortest", str(source),
    ])
    _make(["-f", "lavfi", "-i", "sine=frequency=1200:duration=0.5", str(ding)])

    out = compose_avatar_reel(source, build_ass(WORDS, "Хук"), tmp_path / "sfx_out.mp4", [(ding, 1.0)])

    info = _streams(out)
    assert {stream["codec_type"] for stream in info["streams"]} == {"video", "audio"}
    assert 2.8 <= float(info["format"]["duration"]) <= 3.3
