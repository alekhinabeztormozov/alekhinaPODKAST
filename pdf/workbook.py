from __future__ import annotations

from html import escape
from pathlib import Path
from string import Template

from pydantic import BaseModel, Field

from pdf.renderer import TEMPLATES_DIR, GuideStyle, _logo_block, _side_block, render_html

WORKBOOK_TEMPLATE = TEMPLATES_DIR / "workbook.html"


class LabeledText(BaseModel):
    label: str = Field(description="подпись: Ответ, Если НЕТ, Решение, Что это значит, Что делать, Цифра, Красный флаг")
    text: str


class Block(BaseModel):
    heading: str = Field(description="например: ВОПРОС 1. Есть ли сюрприз? или ПРАВИЛО 2. Заложите подушку")
    fields: list[LabeledText]


class Table(BaseModel):
    title: str = Field(description="например: РЕЗУЛЬТАТ или ПРИМЕР ИЗ МАКДОНАЛДСА, можно пусто")
    columns: list[str]
    rows: list[list[str]]


class WorkbookDoc(BaseModel):
    code: str = Field(description="номер материала, например 3.1")
    kind: str = Field(description="тип: Чек-лист, Бонус, Правила, Разбор")
    title: str
    subtitle: str
    audience: str = Field(description="для кого")
    purpose: str = Field(description="зачем")
    blocks: list[Block]
    tables: list[Table]
    steps: list[str] = Field(description="что делать дальше, короткие действия")


WARNING_LABELS = ("красный флаг", "если", "ошибка")


def _field_html(field: LabeledText) -> str:
    tone = " warn" if field.label.strip().casefold().startswith(WARNING_LABELS) else ""
    return (
        f'<div class="field{tone}"><span class="label">{escape(field.label)}</span>'
        f"<p>{escape(field.text)}</p></div>"
    )


def _split_heading(heading: str) -> tuple[str, str]:
    prefix, dot, rest = heading.partition(".")
    if dot and any(char.isdigit() for char in prefix) and len(prefix) <= 16:
        return prefix.strip(), rest.strip()
    return "", heading.strip()


def _block_html(block: Block, number: int) -> str:
    tag, text = _split_heading(block.heading)
    fields = "".join(_field_html(field) for field in block.fields)
    return (
        f'<section class="block"><div class="num">{number:02d}</div><div class="block-body">'
        f'<div class="tag">{escape(tag)}</div><h2>{escape(text)}</h2>{fields}</div></section>'
    )


def _table_html(table: Table) -> str:
    head = "".join(f"<th>{escape(column)}</th>" for column in table.columns)
    rows = "".join(
        "<tr>" + "".join(f"<td>{escape(cell)}</td>" for cell in row) + "</tr>" for row in table.rows
    )
    title = f"<h3>{escape(table.title)}</h3>" if table.title else ""
    wide = ' class="wide"' if len(table.columns) > 3 else ""
    body = f"<thead><tr>{head}</tr></thead><tbody>{rows}</tbody>"
    return f'<div class="table-wrap">{title}<table{wide}>{body}</table></div>'


def _steps_html(steps: list[str]) -> str:
    if not steps:
        return ""
    items = "".join(f"<li><span>{index}</span><p>{escape(step)}</p></li>" for index, step in enumerate(steps, 1))
    return f'<section class="steps"><h3>Что делать дальше</h3><ol>{items}</ol></section>'


def workbook_html(doc: WorkbookDoc, style: GuideStyle | None = None) -> str:
    style = style or GuideStyle()
    template = Template(WORKBOOK_TEMPLATE.read_text(encoding="utf-8"))
    return template.safe_substitute(
        brand=escape(style.brand),
        accent=style.accent,
        code=escape(doc.code),
        kind=escape(doc.kind),
        title=escape(doc.title),
        subtitle=escape(doc.subtitle),
        audience=escape(doc.audience),
        purpose=escape(doc.purpose),
        blocks="".join(_block_html(block, number) for number, block in enumerate(doc.blocks, 1)),
        tables="".join(_table_html(table) for table in doc.tables),
        steps=_steps_html(doc.steps),
        side=_side_block(),
        logo=_logo_block(),
    )


def render_workbook(doc: WorkbookDoc, out_path: Path, style: GuideStyle | None = None) -> Path:
    return render_html(workbook_html(doc, style), out_path, base_url=TEMPLATES_DIR.as_uri() + "/")
