from __future__ import annotations

import hashlib
from pathlib import Path

import httpx

from config import get_settings

API = "https://api.elevenlabs.io/v1/sound-generation"
SFX_DIR = Path("media/reels/sfx")
MIN_SECONDS = 0.5
MAX_SECONDS = 30.0
PROMPT_INFLUENCE = 0.5
REQUEST_TIMEOUT = 120


class SfxError(RuntimeError):
    pass


def clamp_seconds(seconds: float | None) -> float | None:
    if seconds is None:
        return None
    return min(MAX_SECONDS, max(MIN_SECONDS, float(seconds)))


def sfx_path(description: str, seconds: float | None) -> Path:
    key = f"{description.strip().lower()}|{clamp_seconds(seconds)}"
    return SFX_DIR / f"{hashlib.sha1(key.encode()).hexdigest()[:16]}.mp3"


def sound_request(description: str, seconds: float | None) -> dict:
    body: dict = {"text": description.strip(), "prompt_influence": PROMPT_INFLUENCE}
    if seconds is not None:
        body["duration_seconds"] = clamp_seconds(seconds)
    return body


async def generate_sound(description: str, seconds: float | None = None) -> Path:
    if not description.strip():
        raise SfxError("пустое описание звука")
    api_key = get_settings().elevenlabs_api_key
    if not api_key:
        raise SfxError("ELEVENLABS_API_KEY не задан")
    target = sfx_path(description, seconds)
    if target.exists():
        return target
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        response = await client.post(
            API, headers={"xi-api-key": api_key}, json=sound_request(description, seconds),
            params={"output_format": "mp3_44100_128"},
        )
    if response.status_code != 200 or not response.content:
        raise SfxError(f"ElevenLabs {response.status_code}: {response.text[:300]}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(response.content)
    return target
