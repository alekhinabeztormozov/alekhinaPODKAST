from __future__ import annotations

import asyncio
from pathlib import Path

from config import get_settings
from media.pipeline import AudioProfile, PipelineInputs, process_episode


async def make_episode(
    voice: Path,
    out_path: Path,
    intro: Path | None = None,
    outro: Path | None = None,
    music: Path | None = None,
    profile: AudioProfile | None = None,
) -> Path:
    settings = get_settings()
    inputs = PipelineInputs(
        voice=voice,
        intro=intro,
        outro=outro,
        music=music,
        profile=profile or AudioProfile(),
    )
    return await asyncio.to_thread(
        process_episode,
        inputs,
        out_path,
        settings.ffmpeg_bin,
        settings.ffprobe_bin,
    )
