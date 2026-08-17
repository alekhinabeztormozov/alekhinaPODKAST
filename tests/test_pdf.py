from __future__ import annotations

from pathlib import Path

from bot.handlers.producer import split_guide
from pdf.renderer import render_guide, text_to_html


def test_text_to_html_headings_and_paragraphs():
    html = text_to_html("## Заголовок\n\nПервый абзац.\n\nВторой абзац.")
    assert "<h2>Заголовок</h2>" in html
    assert html.count("<p>") == 2


def test_text_to_html_bullet_list():
    html = text_to_html("Вот ошибки:\n- первая\n- вторая\n- третья")
    assert "<ul>" in html and "</ul>" in html
    assert html.count("<li>") == 3
    assert "<p>Вот ошибки:</p>" in html


def test_text_to_html_list_then_paragraph():
    html = text_to_html("- пункт\n\nобычный абзац")
    assert html.count("<ul>") == 1
    assert "<p>обычный абзац</p>" in html


def test_split_guide_strips_markdown_title():
    title, body = split_guide("## Три ошибки\n\nтело гайда здесь")
    assert title == "Три ошибки"
    assert body == "тело гайда здесь"


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
