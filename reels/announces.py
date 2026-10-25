from __future__ import annotations

from anthropic import AsyncAnthropic
from pydantic import BaseModel

from config import get_settings
from reels.scenarios import MAX_TRANSCRIPT_CHARS, TEMPLATES_DIR

SYSTEM_PROMPT = (TEMPLATES_DIR / "announces_system.md").read_text(encoding="utf-8").strip()
MAX_TOKENS = 8_000
FORBIDDEN = {"«": "\"", "»": "\"", "—": "-"}


class Announces(BaseModel):
    open_channel: str
    closed_channel: str
    vk: str


def clean(text: str) -> str:
    for bad, good in FORBIDDEN.items():
        text = text.replace(bad, good)
    return text.strip()


def build_request(title: str, transcript: str, keyword: str, link: str) -> str:
    parts = [f"Выпуск: {title}"]
    if keyword:
        parts.append(f"Ключевое слово для бота: {keyword}")
    if link:
        parts.append(f"Ссылка на выпуск: {link}")
    parts.append(f"Бот: @{get_settings().bot_username}")
    parts.append(f"Расшифровка выпуска:\n{transcript[:MAX_TRANSCRIPT_CHARS]}")
    return "\n\n".join(parts)


async def generate(title: str, transcript: str, keyword: str = "", link: str = "") -> dict[str, str]:
    settings = get_settings()
    client = AsyncAnthropic(api_key=settings.anthropic_api_key or None)
    response = await client.messages.parse(
        model=settings.reels_model,
        max_tokens=MAX_TOKENS,
        output_config={"effort": "medium"},
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": build_request(title, transcript, keyword, link)}],
        output_format=Announces,
    )
    if response.stop_reason == "refusal" or response.parsed_output is None:
        raise RuntimeError(f"модель не вернула анонсы: {response.stop_reason}")
    return {kind: clean(text) for kind, text in response.parsed_output.model_dump().items()}
