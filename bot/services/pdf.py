from __future__ import annotations

import asyncio
from pathlib import Path

from pdf.renderer import GuideStyle, render_guide


async def build_guide(
    title: str,
    body_text: str,
    out_path: Path,
    logo: Path | None = None,
    brand: str = "АЛЁХИНА БЕЗ ТОРМОЗОВ",
    accent: str = "#1f2a44",
) -> Path:
    style = GuideStyle(brand=brand, accent=accent, logo=logo)
    return await asyncio.to_thread(render_guide, title, body_text, out_path, style)
