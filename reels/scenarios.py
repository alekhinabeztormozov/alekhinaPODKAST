from __future__ import annotations

import base64
from html import escape
from pathlib import Path
from typing import Literal

from anthropic import AsyncAnthropic
from pydantic import BaseModel, Field

from config import get_settings

ReelKind = Literal["why_buy", "trigger_song", "carousel"]

EXAMPLES_DIR = Path("data/reels/examples")
TEMPLATES_DIR = Path(__file__).parent / "templates"
MAX_TRANSCRIPT_CHARS = 120_000
MAX_TOKENS = 16_000

KIND_TITLES: dict[str, str] = {
    "why_buy": "Рилс \"почему покупают\"",
    "trigger_song": "Нейротрек",
    "carousel": "Карусель",
}

SYSTEM_PROMPT = (TEMPLATES_DIR / "scenario_system.md").read_text(encoding="utf-8").strip()
IDEA_PROMPT = (TEMPLATES_DIR / "business_idea.md").read_text(encoding="utf-8").strip()


class Scene(BaseModel):
    seconds: int = Field(description="длительность сцены в секундах")
    voiceover: str = Field(description="что говорит или поет аватар")
    on_screen: str = Field(description="крупный текст на экране, до 6 слов, можно пусто")
    visual: str = Field(description="что в кадре: план, шляпа, предметы, движение")
    sfx: str = Field(
        default="",
        description="звук в начале сцены, коротко по-английски (cash register ding), чаще пусто",
    )


class Slide(BaseModel):
    kicker: str = Field(description="мелкая надпись над заголовком, 1-3 слова, можно пусто")
    title: str = Field(description="крупный заголовок слайда, до 7 слов")
    text: str = Field(description="текст слайда, до 220 знаков, можно пусто")


class Scenario(BaseModel):
    kind: ReelKind
    title: str = Field(description="рабочее название ролика, до 8 слов")
    trigger: str = Field(description="какой нейротриггер или мысль выпуска раскрывает")
    hook: str = Field(description="первая фраза, которая держит зрителя")
    scenes: list[Scene]
    lyrics: str = Field(description="для trigger_song - полный текст песни, для why_buy пусто")
    hat: str = Field(description="какая шляпа или образ на аватаре")
    slides: list[Slide] = Field(description="для carousel - 6-9 слайдов, для остальных пусто")
    caption: str
    hashtags: list[str]


class ScenarioBatch(BaseModel):
    scenarios: list[Scenario]


def load_examples() -> str:
    if not EXAMPLES_DIR.exists():
        return ""
    texts = [path.read_text(encoding="utf-8").strip() for path in sorted(EXAMPLES_DIR.glob("*.txt"))]
    return "\n\n---\n\n".join(text for text in texts if text)


def build_request(title: str, transcript: str, counts: dict[str, int]) -> str:
    plan = ", ".join(f"{kind}: {count}" for kind, count in counts.items() if count)
    parts = [f"Выпуск: {title}", f"Нужно сценариев по форматам - {plan}."]
    examples = load_examples()
    if examples:
        parts.append(f"Примеры сценариев от Юлии, держись их подачи и логики:\n{examples}")
    parts.append(f"Расшифровка выпуска:\n{transcript[:MAX_TRANSCRIPT_CHARS]}")
    return "\n\n".join(parts)


def build_rewrite_request(title: str, transcript: str, scenario: dict, feedback: str) -> str:
    return "\n\n".join([
        f"Выпуск: {title}",
        f"Перепиши один сценарий по правкам Юлии. Формат оставь {scenario.get('kind')}.",
        f"Текущий сценарий:\n{Scenario.model_validate(scenario).model_dump_json(indent=1)}",
        f"Правки Юлии: {feedback}",
        f"Расшифровка выпуска:\n{transcript[:MAX_TRANSCRIPT_CHARS]}",
    ])


def default_counts(total: int) -> dict[str, int]:
    songs = max(1, total // 3)
    carousels = 1 if total >= 3 else 0
    return {"why_buy": total - songs - carousels, "trigger_song": songs, "carousel": carousels}


async def _ask(prompt: str | list[dict]) -> ScenarioBatch:
    settings = get_settings()
    client = AsyncAnthropic(api_key=settings.anthropic_api_key or None)
    response = await client.messages.parse(
        model=settings.reels_model,
        max_tokens=MAX_TOKENS,
        output_config={"effort": "high"},
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
        output_format=ScenarioBatch,
    )
    if response.stop_reason == "refusal" or response.parsed_output is None:
        raise RuntimeError(f"модель не вернула сценарии: {response.stop_reason}")
    return response.parsed_output


def idea_request(description: str, image: bytes | None, archive: str) -> list[dict]:
    instruction = "\n\n".join(part for part in (
        IDEA_PROMPT,
        f"Что прислала Юлия про идею:\n{description}" if description else "",
        f"Выпуски подкаста, на которые можно сослаться:\n{archive}" if archive else "",
    ) if part)
    content: list[dict] = []
    if image:
        content.append({
            "type": "image",
            "source": {"type": "base64", "media_type": "image/jpeg", "data": base64.b64encode(image).decode()},
        })
    content.append({"type": "text", "text": instruction})
    return content


async def from_idea(description: str, image: bytes | None, archive: str = "") -> list[Scenario]:
    batch = await _ask(idea_request(description, image, archive))
    return batch.scenarios


async def generate(title: str, transcript: str, total: int) -> list[Scenario]:
    batch = await _ask(build_request(title, transcript, default_counts(total)))
    return batch.scenarios


async def rewrite(title: str, transcript: str, scenario: dict, feedback: str) -> Scenario:
    batch = await _ask(build_rewrite_request(title, transcript, scenario, feedback))
    if not batch.scenarios:
        raise RuntimeError("модель вернула пустой ответ на правку")
    return batch.scenarios[0]


def voiceover_text(scenario: dict) -> str:
    return " ".join(scene["voiceover"].strip() for scene in scenario.get("scenes", []) if scene.get("voiceover"))


def card_text(scenario: dict) -> str:
    def field(name: str) -> str:
        return escape(str(scenario.get(name, "")))

    lines = [f"<b>{KIND_TITLES.get(scenario.get('kind', ''), 'Ролик')}: {field('title')}</b>"]
    lines.append(f"Триггер: {field('trigger')}")
    lines.append(f"Образ: {field('hat')}")
    lines.append(f"\nХук: {field('hook')}")
    for number, scene in enumerate(scenario.get("scenes", []), start=1):
        screen = f" [{escape(scene['on_screen'])}]" if scene.get("on_screen") else ""
        sound = f" 🔊 {escape(scene['sfx'])}" if scene.get("sfx") else ""
        lines.append(f"{number}. ({scene.get('seconds', 0)} с){screen} {escape(scene.get('voiceover', ''))}{sound}")
    for number, slide in enumerate(scenario.get("slides") or [], start=1):
        text = f" - {escape(slide['text'])}" if slide.get("text") else ""
        lines.append(f"Слайд {number}: <b>{escape(slide.get('title', ''))}</b>{text}")
    if scenario.get("lyrics"):
        lines.append(f"\nТекст песни:\n{field('lyrics')}")
    lines.append(f"\nПодпись: {field('caption')}")
    lines.append(escape(" ".join(f"#{tag.lstrip('#')}" for tag in scenario.get("hashtags", []))))
    return "\n".join(lines)
