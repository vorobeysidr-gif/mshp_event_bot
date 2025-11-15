from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from services.sheets import append_lead_row
from services.backup import backup_to_csv

router = Router()


class QuestStates(StatesGroup):
    question_1 = State()
    question_2 = State()
    question_3 = State()


# Данные квеста
QUEST_INTRO = (
    "🎯 Добро пожаловать в квест \"Загадка Шишки\"!\n\n"
    "Московская школа программистов и Факультет компьютерных наук ВШЭ приглашают Вас пройти небольшой интерактив.\n"
    "На стенде спрятаны ответы на три загадки. Вглядитесь внимательнее: они прячутся в цифрах, фактах и истории нашей школы.\n\n"
    "Проверьте свою внимательность, интуицию и, конечно, любовь к технологиям.\n\n"
    "Готовы начать? 🚀"
)

QUESTION_1 = {
    "text": (
        "🔍 Загадка 1. \"Корни МШП\"\n\n"
        "Я появился там, где ребята писали программы вслепую — без монитора.\n"
        "С тех пор вырос в проект, чьи ученики берут золото на олимпиадах и поступают в лучшие вузы.\n"
        "Где мои истоки?"
    ),
    "hint": "💬 Подсказка: спросите про историю основания Московской школы программистов.",
    "correct": "Мытищи",
    "options": ["Москва", "Королев", "Серпухов", "Мытищи"]
}

QUESTION_2 = {
    "text": (
        "🔍 Загадка 2. \"Язык будущего\"\n\n"
        "Он не требует точек с запятой,\n"
        "его любят школьники и ученые,\n"
        "на нём пишут чат-ботов, нейросети и олимпиады.\n"
        "Он стал главным языком в курсах МШП\n"
        "и первым шагом в мир IT для многих.\n"
        "Что это за язык?"
    ),
    "hint": "💬 Подсказка: посмотрите программу МШП.",
    "correct": "Python",
    "options": ["Python", "C++", "CSS", "Java"]
}

QUESTION_3 = {
    "text": (
        "🔍 Загадка 3. \"Партнёр будущего\"\n\n"
        "Мы помогаем школьникам выбрать путь в IT, а рядом с нами учат Data Science, машинное обучение и аналитику.\n"
        "Вместе мы готовим тех, кто изменит цифровой мир.\n"
        "Кто наш союзник?"
    ),
    "hint": "💬 Подсказка: выясните, с кем сотрудничает МШП.",
    "correct": "ФКН ВШЭ",
    "options": ["Сбер", "ФКН ВШЭ", "Тинькофф", "МГУ"]
}

QUEST_COMPLETE = (
    "🎉 Поздравляем! Вы разгадали все загадки!\n\n"
    "Вы доказали, что умеете мыслить как настоящий айтишник: искать закономерности, анализировать факты и не бояться сложных задач.\n\n"
    "Именно так начинается путь в IT — с любопытства, настойчивости и желания понять, как всё устроено.\n\n"
    "🚀 Продолжайте исследовать, учиться и создавать!\n\n"
    "А если хотите узнать больше — ждём Вас в Московской школе программистов!\n"
    "Будущее технологий начинается с тех, кто ищет ответы."
)


def build_question_keyboard(options: list, show_hint: bool = True) -> InlineKeyboardMarkup:
    """Создает клавиатуру с вариантами ответов"""
    buttons = []
    
    # Добавляем варианты ответов
    for option in options:
        buttons.append([InlineKeyboardButton(text=option, callback_data=f"answer:{option}")])
    
    # Добавляем кнопку подсказки
    if show_hint:
        buttons.append([InlineKeyboardButton(text="💡 Подсказка", callback_data="hint")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def start_quest(message: types.Message, state: FSMContext):
    """Начинает квест после сбора данных"""
    await message.answer(QUEST_INTRO)
    
    # Отправляем первый вопрос
    kb = build_question_keyboard(QUESTION_1["options"])
    await message.answer(QUESTION_1["text"], reply_markup=kb)
    await state.set_state(QuestStates.question_1)


@router.callback_query(QuestStates.question_1, F.data == "hint")
async def hint_q1(cb: types.CallbackQuery):
    """Показывает подсказку для вопроса 1"""
    await cb.answer(QUESTION_1["hint"], show_alert=True)


@router.callback_query(QuestStates.question_1, F.data.startswith("answer:"))
async def answer_q1(cb: types.CallbackQuery, state: FSMContext):
    """Обрабатывает ответ на вопрос 1"""
    answer = cb.data.split(":", 1)[1]
    
    if answer == QUESTION_1["correct"]:
        await cb.message.edit_text(f"✅ {QUESTION_1['text']}\n\n✔️ Правильно! Ответ: {QUESTION_1['correct']}")
        await cb.answer("Верно! 🎉")
        
        # Переходим ко второму вопросу
        kb = build_question_keyboard(QUESTION_2["options"])
        await cb.message.answer(QUESTION_2["text"], reply_markup=kb)
        await state.set_state(QuestStates.question_2)
    else:
        await cb.answer("Неправильно, попробуйте еще раз! 🤔", show_alert=True)


@router.callback_query(QuestStates.question_2, F.data == "hint")
async def hint_q2(cb: types.CallbackQuery):
    """Показывает подсказку для вопроса 2"""
    await cb.answer(QUESTION_2["hint"], show_alert=True)


@router.callback_query(QuestStates.question_2, F.data.startswith("answer:"))
async def answer_q2(cb: types.CallbackQuery, state: FSMContext):
    """Обрабатывает ответ на вопрос 2"""
    answer = cb.data.split(":", 1)[1]
    
    if answer == QUESTION_2["correct"]:
        await cb.message.edit_text(f"✅ {QUESTION_2['text']}\n\n✔️ Правильно! Ответ: {QUESTION_2['correct']}")
        await cb.answer("Верно! 🎉")
        
        # Переходим к третьему вопросу
        kb = build_question_keyboard(QUESTION_3["options"])
        await cb.message.answer(QUESTION_3["text"], reply_markup=kb)
        await state.set_state(QuestStates.question_3)
    else:
        await cb.answer("Неправильно, попробуйте еще раз! 🤔", show_alert=True)


@router.callback_query(QuestStates.question_3, F.data == "hint")
async def hint_q3(cb: types.CallbackQuery):
    """Показывает подсказку для вопроса 3"""
    await cb.answer(QUESTION_3["hint"], show_alert=True)


@router.callback_query(QuestStates.question_3, F.data.startswith("answer:"))
async def answer_q3(cb: types.CallbackQuery, state: FSMContext):
    """Обрабатывает ответ на вопрос 3 и завершает квест"""
    answer = cb.data.split(":", 1)[1]
    
    if answer == QUESTION_3["correct"]:
        await cb.message.edit_text(f"✅ {QUESTION_3['text']}\n\n✔️ Правильно! Ответ: {QUESTION_3['correct']}")
        await cb.answer("Верно! 🎉")
        
        # Показываем финальное сообщение
        await cb.message.answer(QUEST_COMPLETE)
        await state.clear()
    else:
        await cb.answer("Неправильно, попробуйте еще раз! 🤔", show_alert=True)
