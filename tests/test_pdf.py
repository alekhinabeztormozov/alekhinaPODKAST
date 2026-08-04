from __future__ import annotations

from pathlib import Path

from pdf.renderer import render_guide, text_to_html


def test_text_to_html_headings_and_paragraphs():
    html = text_to_html("## Заголовок\n\nПервый абзац.\n\nВторой абзац.")
    assert "<h2>Заголовок</h2>" in html
    assert html.count("<p>") == 2


def test_text_to_html_escapes():
    html = text_to_html("Опасно: <script>alert(1)</script>")
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_text_to_html_linebreaks_within_block():
    html = text_to_html("строка один\nстрока два")
    assert "<br>" in html


def test_render_guide_produces_pdf(tmp_path: Path):
    out = tmp_path / "guide.pdf"
    render_guide("Тест", "## Раздел\n\nАбзац с кириллицей.", out)
    assert out.read_bytes().startswith(b"%PDF")
    assert out.stat().st_size > 1000
