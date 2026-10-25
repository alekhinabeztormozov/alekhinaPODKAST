from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class PdfBonus(StatesGroup):
    waiting_email = State()


class Quiz(StatesGroup):
    in_progress = State()


class Producer(StatesGroup):
    choosing_ambient = State()


class ReelFlow(StatesGroup):
    waiting_episode = State()
    waiting_feedback = State()
    waiting_track = State()
