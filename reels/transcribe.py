from __future__ import annotations

import asyncio
import json
import subprocess
from pathlib import Path

import httpx

from config import get_settings
from media.pipeline import probe_duration
from reels.subtitles import Word

GROQ_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
CHUNK_SECONDS = 20 * 60
TRANSCRIPTS_DIR = Path("data/transcripts")
REQUEST_TIMEOUT = 300


class TranscribeError(RuntimeError):
    pass


def transcript_path(episode_ref: str) -> Path:
    return TRANSCRIPTS_DIR / f"{episode_ref}.json"


def _compress_chunk(source: Path, target: Path, offset: float, length: float) -> None:
    settings = get_settings()
    cmd = [
        settings.ffmpeg_bin, "-hide_banner", "-nostdin", "-y",
        "-ss", f"{offset:.2f}", "-t", f"{length:.2f}", "-i", str(source),
        "-vn", "-ac", "1", "-ar", "16000", "-c:a", "libmp3lame", "-b:a", "32k", str(target),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        raise TranscribeError(f"ffmpeg не сжал кусок {offset:.0f}с: {result.stderr.strip()[-300:]}")


async def _transcribe_chunk(client: httpx.AsyncClient, chunk: Path, with_words: bool) -> dict:
    settings = get_settings()
    data = {"model": settings.transcribe_model, "language": "ru", "response_format": "verbose_json"}
    granularities = ["segment", "word"] if with_words else ["segment"]
    form = [*data.items(), *(("timestamp_granularities[]", g) for g in granularities)]
    with chunk.open("rb") as handle:
        response = await client.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {settings.groq_api_key}"},
            data=form,
            files={"file": (chunk.name, handle, "audio/mpeg")},
        )
    if response.status_code != 200:
        raise TranscribeError(f"Groq {response.status_code}: {response.text[:300]}")
    return response.json()


def _timed(rows: list[dict], text_key: str) -> list[dict]:
    return [{"start": row["start"], "end": row["end"], "text": row[text_key].strip()} for row in rows]


def _shift(rows: list[dict], offset: float) -> list[dict]:
    return [{**row, "start": round(row["start"] + offset, 2), "end": round(row["end"] + offset, 2)} for row in rows]


async def transcribe(source: Path, with_words: bool = False) -> dict:
    if not get_settings().groq_api_key:
        raise TranscribeError("GROQ_API_KEY не задан")
    duration = await asyncio.to_thread(probe_duration, source, get_settings().ffprobe_bin)
    segments: list[dict] = []
    words: list[dict] = []
    work_dir = source.parent
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        offset = 0.0
        while offset < duration:
            chunk = work_dir / f"{source.stem}_part{int(offset)}.mp3"
            length = min(CHUNK_SECONDS, duration - offset)
            await asyncio.to_thread(_compress_chunk, source, chunk, offset, length)
            try:
                payload = await _transcribe_chunk(client, chunk, with_words)
            finally:
                chunk.unlink(missing_ok=True)
            segments += _shift(_timed(payload.get("segments", []), "text"), offset)
            words += _shift(_timed(payload.get("words", []), "word"), offset)
            offset += CHUNK_SECONDS
    return {"segments": segments, "words": words}


async def transcribe_episode(episode_ref: str, source: Path) -> list[dict]:
    target = transcript_path(episode_ref)
    if target.exists():
        return json.loads(target.read_text(encoding="utf-8"))
    result = await transcribe(source)
    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result["segments"], ensure_ascii=False, indent=1), encoding="utf-8")
    return result["segments"]


def load_transcript(episode_ref: str) -> list[dict]:
    target = transcript_path(episode_ref)
    if not target.exists():
        return []
    return json.loads(target.read_text(encoding="utf-8"))


def transcript_text(segments: list[dict]) -> str:
    return "\n".join(segment["text"] for segment in segments if segment.get("text"))


async def words_of(media: Path) -> list[Word]:
    result = await transcribe(media, with_words=True)
    return [Word(row["start"], row["end"], row["text"]) for row in result["words"] if row["text"]]
