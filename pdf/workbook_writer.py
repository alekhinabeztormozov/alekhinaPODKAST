from __future__ import annotations

import io

from anthropic import AsyncAnthropic
from pypdf import PdfReader

from config import get_settings
from pdf.renderer import TEMPLATES_DIR
from pdf.workbook import WorkbookDoc

SYSTEM_PROMPT = (TEMPLATES_DIR / "workbook_system.md").read_text(encoding="utf-8").strip()
MAX_SOURCE_CHARS = 120_000
MAX_TOKENS = 16_000
FORBIDDEN = {"«": "\"", "»": "\"", "—": "-"}


def from_transcript_request(title: str, code: str, transcript: str) -> str:
    return "\n\n".join([
        f"Сделай материал PDF {code} к выпуску \"{title}\" по главной практической мысли выпуска.",
        f"Расшифровка выпуска:\n{transcript[:MAX_SOURCE_CHARS]}",
    ])


def restyle_request(source_text: str) -> str:
    return "\n\n".join([
        "Это готовый материал Юлии, выгруженный из документа. Разложи его по структуре без изменений смысла: "
        "сохрани ее формулировки, номера, таблицы и все пункты, ничего не добавляй и не сокращай. "
        "Номер материала возьми из заголовка.",
        f"Текст материала:\n{source_text[:MAX_SOURCE_CHARS]}",
    ])


def _clean(value):
    if isinstance(value, str):
        for bad, good in FORBIDDEN.items():
            value = value.replace(bad, good)
        return value
    if isinstance(value, list):
        return [_clean(item) for item in value]
    if isinstance(value, dict):
        return {key: _clean(item) for key, item in value.items()}
    return value


async def _ask(prompt: str) -> WorkbookDoc:
    settings = get_settings()
    client = AsyncAnthropic(api_key=settings.anthropic_api_key or None)
    response = await client.messages.parse(
        model=settings.reels_model,
        max_tokens=MAX_TOKENS,
        output_config={"effort": "high"},
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
        output_format=WorkbookDoc,
    )
    if response.stop_reason == "refusal" or response.parsed_output is None:
        raise RuntimeError(f"модель не вернула материал: {response.stop_reason}")
    return WorkbookDoc.model_validate(_clean(response.parsed_output.model_dump()))


async def from_transcript(title: str, code: str, transcript: str) -> WorkbookDoc:
    return await _ask(from_transcript_request(title, code, transcript))


async def restyle(source_text: str) -> WorkbookDoc:
    return await _ask(restyle_request(source_text))


def pdf_text(data: bytes) -> str:
    reader = PdfReader(io.BytesIO(data))
    return "\n".join(page.extract_text() or "" for page in reader.pages).strip()
