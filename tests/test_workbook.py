from __future__ import annotations

from pdf import workbook_writer
from pdf.workbook import Block, LabeledText, Table, WorkbookDoc, render_workbook, workbook_html

DOC = WorkbookDoc(
    code="3.1",
    kind="Чек-лист",
    title="HAPPY <детский>",
    subtitle="7 вопросов для детского продукта",
    audience="Владельцы бизнеса",
    purpose="Создать продукт, который захотят",
    blocks=[
        Block(heading="ВОПРОС 1. Есть ли сюрприз?", fields=[
            LabeledText(label="Ответ", text="ДА / НЕТ"),
            LabeledText(label="Если НЕТ", text="Вы теряете дофамин."),
            LabeledText(label="Решение", text="Добавьте игрушку."),
        ]),
        Block(heading="Без номера в заголовке", fields=[LabeledText(label="Красный флаг", text="Нет подушки.")]),
    ],
    tables=[
        Table(title="Результат", columns=["Было", "Стало"], rows=[["Без сюрприза", "С сюрпризом"]]),
        Table(title="", columns=["A", "B", "C", "D"], rows=[["1", "2", "3", "4"]]),
    ],
    steps=["Добавьте сюрприз.", "Создайте серию."],
)


def test_html_numbers_blocks_and_splits_heading():
    html = workbook_html(DOC)
    assert '<div class="num">01</div>' in html
    assert '<div class="tag">ВОПРОС 1</div><h2>Есть ли сюрприз?</h2>' in html
    assert '<div class="tag"></div><h2>Без номера в заголовке</h2>' in html


def test_html_marks_warnings_and_escapes():
    html = workbook_html(DOC)
    assert html.count('class="field warn"') == 2
    assert "HAPPY &lt;детский&gt;" in html
    assert "PDF 3.1 · Чек-лист" in html


def test_html_tables_and_steps():
    html = workbook_html(DOC)
    assert "<th>Было</th><th>Стало</th>" in html
    assert '<table class="wide">' in html
    assert "<li><span>2</span><p>Создайте серию.</p></li>" in html


def test_render_and_read_back(tmp_path):
    out = render_workbook(DOC, tmp_path / "wb.pdf")
    text = workbook_writer.pdf_text(out.read_bytes())
    assert "сюрприз" in text
    assert "Создайте серию." in text


def test_requests_carry_source():
    assert "ничего не добавляй" in workbook_writer.restyle_request("ТЕКСТ")
    assert workbook_writer.restyle_request("ТЕКСТ").endswith("ТЕКСТ")
    prompt = workbook_writer.from_transcript_request("Мак Э3", "3.1", "расшифровка")
    assert "PDF 3.1" in prompt and "\"Мак Э3\"" in prompt


def test_clean_replaces_marks_deeply():
    cleaned = workbook_writer._clean({"a": ["«да» — нет"], "b": 3})
    assert cleaned == {"a": ["\"да\" - нет"], "b": 3}
