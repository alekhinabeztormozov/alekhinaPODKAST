from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from bot.content import DEFAULT_QUIZ, QUIZ_INTRO, quiz_result
from bot.keyboards.common import offer_closed, quiz_intro_kb, quiz_kb
from bot.services import sheets
from bot.states.flows import Quiz
from bot.ui import show

router = Router(name="quiz")


@router.callback_query(F.data == "quiz")
async def quiz_intro(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await show(callback, QUIZ_INTRO, quiz_intro_kb())


@router.callback_query(F.data == "quiz:go")
async def start_quiz(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Quiz.in_progress)
    await state.update_data(idx=0, answers=[])
    await _ask(callback, 0)


@router.callback_query(F.data.startswith("quiz:ans:"), Quiz.in_progress)
async def answer_quiz(callback: CallbackQuery, state: FSMContext) -> None:
    _, _, raw_index, raw_option = callback.data.split(":")
    index, option = int(raw_index), int(raw_option)

    data = await state.get_data()
    if index != data.get("idx", 0):
        await callback.answer()
        return

    answers: list[int] = list(data.get("answers", []))
    answers.append(option)
    next_index = index + 1

    if next_index < len(DEFAULT_QUIZ.questions):
        await state.update_data(idx=next_index, answers=answers)
        await _ask(callback, next_index)
        return

    await state.clear()
    result = quiz_result(answers)
    if callback.from_user is not None:
        await sheets.add_contact(
            tg_id=callback.from_user.id,
            name=callback.from_user.full_name,
            source="quiz",
            quiz_result=result,
        )
    await show(callback, result, offer_closed())


async def _ask(callback: CallbackQuery, index: int) -> None:
    question = DEFAULT_QUIZ.questions[index]
    total = len(DEFAULT_QUIZ.questions)
    header = f"🧠 <b>Вопрос {index + 1} из {total}</b>\n\n{question.text}"
    await show(callback, header, quiz_kb(question, index))
