from __future__ import annotations

import asyncio
from functools import lru_cache
from pathlib import Path

from loguru import logger

from pdf.renderer import GuideStyle, render_guide

DEFAULT_LOGO = Path(__file__).resolve().parents[2] / "pdf" / "assets" / "logo.png"


@lru_cache
def _transparent_logo() -> Path | None:
    if not DEFAULT_LOGO.exists():
        return None
    try:
        from PIL import Image

        with Image.open(DEFAULT_LOGO) as image:
            if image.mode not in ("RGBA", "LA") and not (
                image.mode == "P" and "transparency" in image.info
            ):
                logger.warning("Логотип без альфа-канала — использую фирменный вордмарк.")
                return None
            alpha = image.convert("RGBA").getchannel("A")
            if alpha.getextrema()[0] > 250:
                logger.warning("Логотип непрозрачный (фон запечён) — использую вордмарк.")
                return None
    except Exception as exc:
        logger.warning("Не проверил логотип ({}) — использую вордмарк.", exc)
        return None
    return DEFAULT_LOGO


async def build_guide(
    title: str,
    body_text: str,
    out_path: Path,
    logo: Path | None = None,
    brand: str = "АЛЁХИНА БЕЗ ТОРМОЗОВ",
    accent: str = "#E10600",
) -> Path:
    style = GuideStyle(brand=brand, accent=accent, logo=logo or _transparent_logo())
    return await asyncio.to_thread(render_guide, title, body_text, out_path, style)
