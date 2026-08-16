from __future__ import annotations

import base64
import html
import mimetypes
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from string import Template

_GTK_CANDIDATES = (
    os.environ.get("GTK_BIN_DIR", ""),
    r"C:\msys64\mingw64\bin",
    r"C:\Program Files\GTK3-Runtime Win64\bin",
)

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
DEFAULT_TEMPLATE = TEMPLATES_DIR / "guide.html"
FONTS_DIR = Path(__file__).resolve().parent / "fonts"
BRUSH_ASSET = Path(__file__).resolve().parent / "assets" / "brush.png"


@dataclass
class GuideStyle:
    brand: str = "АЛЁХИНА БЕЗ ТОРМОЗОВ"
    accent: str = "#E10600"


class PdfError(RuntimeError):
    pass


def text_to_html(text: str) -> str:
    rendered: list[str] = []
    paragraph: list[str] = []

    def flush() -> None:
        if paragraph:
            rendered.append("<p>" + "<br>".join(paragraph) + "</p>")
            paragraph.clear()

    for raw in text.replace("\r\n", "\n").split("\n"):
        line = raw.strip()
        if not line:
            flush()
        elif line.startswith("## "):
            flush()
            rendered.append(f"<h2>{html.escape(line[3:].strip())}</h2>")
        elif line.startswith("# "):
            flush()
            rendered.append(f"<h2>{html.escape(line[2:].strip())}</h2>")
        else:
            paragraph.append(html.escape(line))
    flush()
    return "\n".join(rendered)


def _data_uri(path: Path) -> str:
    mime = mimetypes.guess_type(str(path))[0] or "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def _brush_block() -> str:
    if not BRUSH_ASSET.exists():
        return ""
    return f'<img src="{_data_uri(BRUSH_ASSET)}" alt="">'


def render_guide(
    title: str,
    body_text: str,
    out_path: Path,
    style: GuideStyle | None = None,
    template_path: Path = DEFAULT_TEMPLATE,
) -> Path:
    style = style or GuideStyle()
    if not template_path.exists():
        raise PdfError(f"шаблон не найден: {template_path}")

    template = Template(template_path.read_text(encoding="utf-8"))
    document = template.safe_substitute(
        brand=html.escape(style.brand),
        accent=style.accent,
        title=html.escape(title),
        body=text_to_html(body_text),
        brush=_brush_block(),
    )
    return render_html(document, out_path, base_url=str(template_path.parent))


def _ensure_gtk() -> None:
    if sys.platform != "win32":
        return
    for directory in _GTK_CANDIDATES:
        if directory and Path(directory).is_dir():
            os.environ["PATH"] = directory + os.pathsep + os.environ.get("PATH", "")
            try:
                os.add_dll_directory(directory)
            except (OSError, AttributeError):
                pass
            return


def render_html(document: str, out_path: Path, base_url: str | None = None) -> Path:
    _ensure_gtk()
    try:
        from weasyprint import HTML
    except ImportError as exc:
        raise PdfError(
            "WeasyPrint не установлен или не найдены GTK-библиотеки. "
            "См. requirements.txt и установку GTK для Windows."
        ) from exc

    out_path.parent.mkdir(parents=True, exist_ok=True)
    HTML(string=document, base_url=base_url).write_pdf(str(out_path))
    if not out_path.exists() or out_path.stat().st_size == 0:
        raise PdfError(f"PDF не создан: {out_path}")
    return out_path
