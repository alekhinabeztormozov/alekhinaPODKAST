from __future__ import annotations

import asyncio
from pathlib import Path

from pdf.renderer import GuideStyle, render_guide


async def build_guide(
    title: str,
    body_text: str,
    out_path: Path,
    brand: str = "АЛЁХИНА БЕЗ ТОРМОЗОВ",
    accent: str = "#E10600",
) -> Path:
    style = GuideStyle(brand=brand, accent=accent)
    return await asyncio.to_thread(render_guide, title, body_text, out_path, style)
