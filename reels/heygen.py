from __future__ import annotations

from pathlib import Path

import httpx

from config import get_settings

API = "https://api.heygen.com"
MAX_INPUT_CHARS = 1500
REQUEST_TIMEOUT = 60
DOWNLOAD_TIMEOUT = 300


class HeygenError(RuntimeError):
    pass


def _headers() -> dict[str, str]:
    settings = get_settings()
    if not settings.heygen_api_key:
        raise HeygenError("HEYGEN_API_KEY не задан")
    return {"X-Api-Key": settings.heygen_api_key, "Content-Type": "application/json"}


def video_request(text: str) -> dict:
    settings = get_settings()
    if not settings.heygen_avatar_id or not settings.heygen_voice_id:
        raise HeygenError("HEYGEN_AVATAR_ID и HEYGEN_VOICE_ID не заданы")
    return {
        "video_inputs": [{
            "character": {"type": "avatar", "avatar_id": settings.heygen_avatar_id, "avatar_style": "normal"},
            "voice": {"type": "text", "voice_id": settings.heygen_voice_id, "input_text": text[:MAX_INPUT_CHARS]},
        }],
        "dimension": {"width": 1080, "height": 1920},
        "test": settings.heygen_test_mode,
    }


async def start_video(text: str) -> str:
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        response = await client.post(f"{API}/v2/video/generate", headers=_headers(), json=video_request(text))
    payload = response.json() if response.content else {}
    video_id = (payload.get("data") or {}).get("video_id")
    if response.status_code != 200 or not video_id:
        raise HeygenError(f"HeyGen не принял ролик {response.status_code}: {response.text[:300]}")
    return video_id


async def video_status(video_id: str) -> tuple[str, str]:
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        response = await client.get(
            f"{API}/v1/video_status.get", headers=_headers(), params={"video_id": video_id}
        )
    if response.status_code != 200:
        raise HeygenError(f"HeyGen статус {response.status_code}: {response.text[:300]}")
    data = response.json().get("data") or {}
    status = data.get("status", "")
    if status == "failed":
        raise HeygenError(f"HeyGen не собрал ролик: {data.get('error')}")
    return status, data.get("video_url") or ""


async def download(url: str, target: Path) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    async with httpx.AsyncClient(timeout=DOWNLOAD_TIMEOUT, follow_redirects=True) as client:
        async with client.stream("GET", url) as response:
            response.raise_for_status()
            with target.open("wb") as handle:
                async for chunk in response.aiter_bytes():
                    handle.write(chunk)
    return target
