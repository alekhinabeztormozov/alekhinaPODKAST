from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class PdfBonus(StatesGroup):
    waiting_email = State()


class Quiz(StatesGroup):
    in_progress = State()


class Producer(StatesGroup):
    choosing_ambient = State()
