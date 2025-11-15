from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from services.sheets import append_lead_row
from services.backup import backup_to_csv
from .quest import start_quest
import re

router = Router()


class LeadForm(StatesGroup):
    agreement = State()
    name = State()
    contact = State()
    age = State()
    is_student = State()
        # time = State()  # Закомментировано: может понадобиться в будущем


# Старт перенесён в handlers/agreement.py, чтобы сначала получить согласия.


@router.message(LeadForm.name)
async def handle_name(message: types.Message, state: FSMContext):
    
    name = (message.text or "").strip()
    # Разрешаем буквы (RU/EN), пробелы и дефисы; длина 2..50
    if not name or not re.fullmatch(r"[A-Za-zА-Яа-яЁё\-\s]{2,50}", name):
        await message.answer(
            "Пожалуйста, укажите имя буквами (2–50 символов). Допустимы русские/английские символы, пробелы и дефис."
        )
        return
    await state.update_data(name=name)

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Отправить контакт", request_contact=True)],
            [KeyboardButton(text="Ввести номер вручную")],
        ],
        resize_keyboard=True,
    )
    await message.answer(
        (
            "Пожалуйста, отправьте свой контакт 👇 \n"
            "\n"
            "Вы можете:\n"
            "• Нажать на значок 'скрепка' -> 'Контакт' и выбрать свой контакт;\n"
            "• Нажать 'Ввести номер вручную' и прислать номер в формате +7XXXXXXXXXX или 8XXXXXXXXXX.\n"
            "Примеры: +79991234567 или 89161234567"
        ),
        reply_markup=kb,
    )
    await state.set_state(LeadForm.contact)


@router.message(LeadForm.contact, F.contact)
async def handle_contact(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)
    await message.answer(
        "Отлично! Сколько учащемуся лет?", 
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(LeadForm.age)


@router.message(LeadForm.contact, F.text)
async def handle_phone_text(message: types.Message, state: FSMContext):
    import re

    raw = (message.text or "").strip()
    if not raw or raw.lower() == "ввести номер вручную":
        await message.answer(
            "Пожалуйста, пришлите номер в формате +7XXXXXXXXXX или 8XXXXXXXXXX. Примеры: +79991234567 или 89161234567"
        )
        return

    digits = re.sub(r"\D", "", raw)
    fixed = None
    if len(digits) == 11 and digits.startswith("8"):
        fixed = "+7" + digits[1:]
    elif len(digits) == 11 and digits.startswith("7"):
        fixed = "+" + digits
    elif len(digits) == 10 and digits.startswith("9"):
        fixed = "+7" + digits
    elif raw.startswith("+7") and re.fullmatch(r"\+7\d{10}", raw.replace(" ", "")):
        fixed = raw.replace(" ", "")

    if not fixed:
        await message.answer(
            "⚠️ Пожалуйста, введите корректный номер телефона:" \
            "\n" \
            "• В формате +7XXXXXXXXXX. Пример: +79991234567 \n"
            "или \n"
            "• в формате 8XXXXXXXXXX"
        )
        return

    await state.update_data(phone=fixed)
    await message.answer(
        "Принято! Сколько лет учащемуся?", reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(LeadForm.age)


@router.message(LeadForm.age)
async def ask_is_student(message: types.Message, state: FSMContext):
    age_text = (message.text or "").strip()
    if not age_text.isdigit():
        await message.answer("Возраст должен быть положительным числом. Например: 16")
        return
    age = int(age_text)
    if age < 1 or age > 18:
        await message.answer("Возраст должен быть от 1 до 18 лет.")
        return
    await state.update_data(age=str(age))

    # Вопрос: учится ли ребенок у нас
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Да")], [KeyboardButton(text="Еще нет")]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await message.answer("Ребенок учится у нас?", reply_markup=kb)
    await state.set_state(LeadForm.is_student)

    # Закомментировано: выбор времени может понадобиться в будущем
    # times = [
    #     "13:00 - 14:00", 
    #     "14:30 - 15:30",
    #     "16:00 - 17:00"
    # ]

@router.message(LeadForm.is_student, F.text.in_({"Да", "Еще нет"}))
async def finish_registration(message: types.Message, state: FSMContext):
    await state.update_data(is_mshp_student=message.text)
    
    # Сохраняем данные в таблицу ПЕРЕД квестом
    data = await state.get_data()
    try:
        append_lead_row(data)
    except Exception:
        backup_to_csv(data)
    
    # Убираем клавиатуру
    await message.answer("Отлично! Спасибо за информацию! 😊", reply_markup=types.ReplyKeyboardRemove())
    
    # Запускаем квест
    await start_quest(message, state)

@router.message(LeadForm.is_student)
async def is_student_invalid(message: types.Message, state: FSMContext):
    await message.answer("Пожалуйста, выберите вариант кнопкой: Да или Еще нет.")


    # Закомментировано: выбор времени мастер-класса (может понадобиться в будущем)
    # @router.message(LeadForm.time, F.text.in_({
    #     time for time in times
    # }))
    # 
    # async def finish_with_time(message: types.Message, state: FSMContext):
    #     await state.update_data(time=message.text)
    # 
    #     data = await state.get_data()
    #     try:
    #         append_lead_row(data)
    #     except Exception:
    #         backup_to_csv(data)
    # 
    #     name = data.get("name", "")
    #     time_slot = data.get("time", "")
    #     final_text = (
    #         f"Спасибо за регистрацию, {name}!\n\n"
    #         f"🕒 Время: {time_slot}\n\n"
    #         f"Ждём вас на мастер-классе!"
    #     )
    #     await message.answer(final_text, reply_markup=types.ReplyKeyboardRemove())
    #     await state.clear()
    # 
    # 
    # @router.message(LeadForm.time)
    # async def time_invalid(message: types.Message, state: FSMContext):
    #     await message.answer(
    #         "Пожалуйста, выберите один из предложенных вариантов времени кнопкой ниже."
    #     )

