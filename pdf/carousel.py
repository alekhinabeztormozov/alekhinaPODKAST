from __future__ import annotations

from html import escape
from pathlib import Path
from string import Template

import pymupdf

from pdf.renderer import LOGO_ASSET, SIDE_ASSET, TEMPLATES_DIR, GuideStyle, _data_uri, render_html

CAROUSEL_TEMPLATE = TEMPLATES_DIR / "carousel.html"
SLIDE_WIDTH_PX = 1080
CSS_PX_TO_PT = 0.75
FALLBACK_LOGO = LOGO_ASSET.with_name("logo.png")


def _image(path: Path, css_class: str) -> str:
    if not path.exists():
        return ""
    return f'<img class="{css_class}" src="{_data_uri(path)}" alt="">'


def _logo() -> str:
    return _image(LOGO_ASSET if LOGO_ASSET.exists() else FALLBACK_LOGO, "logo")


def _text(slide: dict) -> str:
    return f'<p class="text">{escape(slide["text"])}</p>' if slide.get("text") else ""


def _kicker(slide: dict) -> str:
    return f'<div class="kicker">{escape(slide["kicker"])}</div>' if slide.get("kicker") else ""


def cover_html(slide: dict) -> str:
    return (
        f'<section class="slide cover">{_image(SIDE_ASSET, "brush")}{_kicker(slide)}'
        f'<h1>{escape(slide.get("title", ""))}</h1>{_text(slide)}'
        f'<div class="swipe">Листайте →</div>{_logo()}</section>'
    )


def body_html(slide: dict, number: int, total: int, brand: str) -> str:
    return (
        f'<section class="slide"><div class="num">{number:02d}</div>{_kicker(slide)}'
        f'<h2>{escape(slide.get("title", ""))}</h2><div class="rule"></div>{_text(slide)}'
        f'<div class="footer">{escape(brand)} · {number}/{total}</div>{_logo()}</section>'
    )


def final_html(slide: dict, number: int, total: int, brand: str, bot_username: str) -> str:
    return (
        f'<section class="slide final">{_kicker(slide)}<h2>{escape(slide.get("title", ""))}</h2>'
        f'{_text(slide)}<div class="cta">@{escape(bot_username)}</div>'
        f'<div class="footer">{escape(brand)} · {number}/{total}</div></section>'
    )


def carousel_html(slides: list[dict], bot_username: str, style: GuideStyle | None = None) -> str:
    style = style or GuideStyle()
    total = len(slides)
    parts = []
    for number, slide in enumerate(slides, start=1):
        if number == 1:
            parts.append(cover_html(slide))
        elif number == total:
            parts.append(final_html(slide, number, total, style.brand, bot_username))
        else:
            parts.append(body_html(slide, number, total, style.brand))
    template = Template(CAROUSEL_TEMPLATE.read_text(encoding="utf-8"))
    return template.safe_substitute(accent=style.accent, slides="\n".join(parts))


def render_carousel(slides: list[dict], out_dir: Path, bot_username: str, prefix: str = "slide") -> list[Path]:
    if not slides:
        raise ValueError("в карусели нет слайдов")
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = out_dir / f"{prefix}.pdf"
    render_html(carousel_html(slides, bot_username), pdf_path, base_url=TEMPLATES_DIR.as_uri() + "/")
    zoom = SLIDE_WIDTH_PX / (SLIDE_WIDTH_PX * CSS_PX_TO_PT)
    images = []
    with pymupdf.open(pdf_path) as document:
        for index, page in enumerate(document, start=1):
            target = out_dir / f"{prefix}_{index:02d}.png"
            page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom)).save(target)
            images.append(target)
    pdf_path.unlink(missing_ok=True)
    return images
