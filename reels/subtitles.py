from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

TEMPLATES_DIR = Path(__file__).parent / "templates"

MAX_WORDS_PER_LINE = 3
MAX_CHARS_PER_LINE = 18
MAX_PAUSE = 0.6
HOOK_SECONDS = 3.0

ASS_HEADER = (TEMPLATES_DIR / "subtitles_header.ass").read_text(encoding="utf-8")


@dataclass(frozen=True)
class Word:
    start: float
    end: float
    text: str


def ass_time(seconds: float) -> str:
    centis = max(0, round(seconds * 100))
    hours, rest = divmod(centis, 360_000)
    minutes, rest = divmod(rest, 6_000)
    secs, centis = divmod(rest, 100)
    return f"{hours}:{minutes:02d}:{secs:02d}.{centis:02d}"


def escape(text: str) -> str:
    return text.replace("\\", "").replace("{", "(").replace("}", ")").replace("\n", " ").strip()


def _closes_line(line: list[Word], following: Word | None) -> bool:
    if len(line) >= MAX_WORDS_PER_LINE:
        return True
    if sum(len(word.text) + 1 for word in line) >= MAX_CHARS_PER_LINE:
        return True
    if line[-1].text.rstrip().endswith((".", "!", "?", ",", ":")):
        return True
    return following is not None and following.start - line[-1].end > MAX_PAUSE


def group_lines(words: list[Word]) -> list[list[Word]]:
    lines: list[list[Word]] = []
    current: list[Word] = []
    for index, word in enumerate(words):
        if not word.text.strip():
            continue
        current.append(word)
        following = words[index + 1] if index + 1 < len(words) else None
        if _closes_line(current, following):
            lines.append(current)
            current = []
    if current:
        lines.append(current)
    return lines


def karaoke_line(line: list[Word]) -> str:
    parts = []
    for word in line:
        duration = max(1, round((word.end - word.start) * 100))
        parts.append(f"{{\\kf{duration}}}{escape(word.text).upper()}")
    return " ".join(parts)


def build_ass(words: list[Word], hook: str = "", shift: float = 0.0) -> str:
    events = []
    if hook:
        events.append(f"Dialogue: 1,{ass_time(0)},{ass_time(HOOK_SECONDS)},Hook,,0,0,0,,{escape(hook).upper()}")
    for line in group_lines(words):
        start = line[0].start + shift
        end = line[-1].end + shift
        events.append(f"Dialogue: 0,{ass_time(start)},{ass_time(end)},Sub,,0,0,0,,{karaoke_line(line)}")
    return ASS_HEADER + "\n".join(events) + "\n"


def words_from_segments(segments: list[dict]) -> list[Word]:
    words: list[Word] = []
    for segment in segments:
        tokens = segment.get("text", "").split()
        if not tokens:
            continue
        start, end = float(segment["start"]), float(segment["end"])
        step = (end - start) / len(tokens)
        for index, token in enumerate(tokens):
            words.append(Word(start + index * step, start + (index + 1) * step, token))
    return words
