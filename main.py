import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton, 
    InlineKeyboardMarkup, InlineKeyboardButton,
    FSInputFile
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import TOKEN

from google.oauth2.service_account import Credentials
import gspread
import datetime
import logging
import os
import time

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация Google Sheets
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
try:
    creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
    gc = gspread.authorize(creds)
    sheet = gc.open_by_key("1Ae3hEdYDLr3VXM7_7_b3IHv0dL9RjfVlpHhJUOQL8sY").sheet1
    logger.info("Successfully connected to Google Sheets")
except Exception as e:
    logger.error(f"Failed to initialize Google Sheets: {e}")
    sheet = None

# Инициализация бота
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- Состояния ---
class LeadForm(StatesGroup):
    privacy_accept = State()
    name = State()
    contact = State()
    age = State()        # Возраст ребенка
    is_mshp_student = State()  # Учится ли в МШП
    time = State()

# --- Установка команд в меню ---
async def set_commands(bot: Bot):
    commands = [
        types.BotCommand(command="start", description="Начать запись на мастер-класс")
    ]
    await bot.set_my_commands(commands)

def get_agreement_keyboard(privacy_checked: bool = False, agreement_checked: bool = False):
    builder = InlineKeyboardBuilder()
    
    # Кнопки для политики конфиденциальности
    privacy_text = "☑️" if privacy_checked else "⬜️"
    builder.button(
        text=f"{privacy_text} Политика конфиденциальности",
        callback_data="toggle_privacy"
    )
    
    # Кнопки для согласия на обработку
    agreement_text = "☑️" if agreement_checked else "⬜️"
    builder.button(
        text=f"{agreement_text} Согласие на обработку персональных данных",
        callback_data="toggle_agreement"
    )
    
    # Добавляем кнопки как отдельные строки
    builder.adjust(1)
    
    # Добавляем ссылки на документы
    builder.row(
        InlineKeyboardButton(
            text="📄 Открыть политику",
            url="https://informatics.ru/files/documents/Политика_конфиденциальности_АНО_ДО_МШП.pdf"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="📄 Открыть согласие",
            callback_data="show_agreement_doc"
        )
    )
    
    # Кнопка подтверждения (активна только если оба пункта отмечены)
    if privacy_checked and agreement_checked:
        builder.row(InlineKeyboardButton(
            text="✅ Подтвердить",
            callback_data="confirm_all"
        ))
    
    return builder.as_markup()

# --- Старт ---
@dp.message(CommandStart())
async def start(message: types.Message, state: FSMContext):
    await state.set_state(LeadForm.privacy_accept)
    await state.update_data(privacy_checked=False, agreement_checked=False)
    
    text = (
        "Добрый день! 😊\n\n"
        "Для записи на мастер-класс необходимо ваше согласие с документами ниже.\n"
        "Пожалуйста, ознакомьтесь и отметьте оба пункта:"
    )
    
    await message.answer(
        text,
        reply_markup=get_agreement_keyboard(),
        disable_web_page_preview=True
    )

# --- Обработка нажатий на чекбоксы ---
@dp.callback_query(lambda c: c.data in ["toggle_privacy", "toggle_agreement"])
async def handle_agreement_toggle(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    privacy_checked = data.get('privacy_checked', False)
    agreement_checked = data.get('agreement_checked', False)
    
    if callback.data == "toggle_privacy":
        privacy_checked = not privacy_checked
        await state.update_data(privacy_checked=privacy_checked)
    else:
        agreement_checked = not agreement_checked
        await state.update_data(agreement_checked=agreement_checked)
    
    await callback.message.edit_reply_markup(
        reply_markup=get_agreement_keyboard(privacy_checked, agreement_checked)
    )
    await callback.answer()

# --- Отправка документа согласия ---
@dp.callback_query(lambda c: c.data == "show_agreement_doc")
async def send_agreement_document(callback: types.CallbackQuery):
    """
    Отправка локального файла согласия.
    - Предпочитает PDF, если он присутствует.
    - Фоллбек на DOCX при отсутствии PDF.
    - Использует FSInputFile с ASCII-именем для надёжной отправки.
    """
    base_dir = os.getcwd()
    pdf_path = os.path.join(base_dir, "согласние_на_обработку_Москва_на_сайт_для_маркетинга.pdf")
    docx_path = os.path.join(base_dir, "согласние_на_обработку_Москва_на_сайт_для_маркетинга.docx")

    # Выбираем файл для отправки
    if os.path.exists(pdf_path):
        file_path = pdf_path
        ascii_name = "agreement.pdf"
    elif os.path.exists(docx_path):
        file_path = docx_path
        ascii_name = "agreement.docx"
    else:
        logger.error("Agreement file not found: %s or %s", pdf_path, docx_path)
        await callback.message.answer("Файл согласия не найден. Пожалуйста, сообщите администратору.")
        await callback.answer()
        return

    try:
        size_bytes = os.path.getsize(file_path)
        logger.info("Found agreement file: %s (%.2f KB)", file_path, size_bytes / 1024)

        # Отправляем индикатор загрузки
        status_message = await callback.message.answer("⏳ Отправка файла...")

        try:
            input_file = types.FSInputFile(file_path, filename=ascii_name)
            start_ts = time.time()
            await callback.message.answer_document(document=input_file, caption="Согласие на обработку персональных данных")
            elapsed = time.time() - start_ts
            logger.info("Agreement file sent successfully in %.2fs", elapsed)
            # Удаляем индикатор загрузки
            try:
                await status_message.delete()
            except Exception:
                pass
        except Exception as send_exc:
            logger.exception("Error sending agreement file: %s", send_exc)
            try:
                await status_message.edit_text("❌ Не удалось отправить файл. Попробуйте через несколько минут.")
            except Exception:
                # если не получилось редактировать — отправим отдельное сообщение
                await callback.message.answer("❌ Не удалось отправить файл. Попробуйте через несколько минут.")

    except Exception as e:
        logger.exception("Unexpected error while preparing agreement file: %s", e)
        await callback.message.answer("Произошла ошибка при подготовке файла. Пожалуйста, попробуйте позже.")

    await callback.answer()

# --- Обработка подтверждения ---
@dp.callback_query(lambda c: c.data == "confirm_all")
async def handle_agreement_confirm(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if data.get('privacy_checked') and data.get('agreement_checked'):
        await callback.message.delete()  # Удаляем сообщение с соглашениями
        await callback.message.answer("Спасибо! Как Вас зовут?")
        await state.set_state(LeadForm.name)
    await callback.answer()

# --- Имя ---
@dp.message(LeadForm.name)
async def ask_contact(message: types.Message, state: FSMContext):
    # Validate name: must contain at least one letter (Cyrillic or Latin)
    name = (message.text or "").strip()
    import re
    if not name or not re.search(r"[A-Za-zА-Яа-яЁё]", name):
        await message.answer("Пожалуйста, введите корректное имя — минимум одна буква. Как Вас зовут?")
        return

    await state.update_data(name=name)
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Отправить контакт (через скрепку)")],
            [KeyboardButton(text="Ввести номер вручную")]
        ],
        resize_keyboard=True
    )
    await message.answer(
        "Пожалуйста, отправьте свой контакт 👇\n\n" 
        "Вы можете: \n"
        "• Нажать на значок 'скрепка' -> 'Контакт' и выбрать свой контакт;\n"
        "• Или выбрать 'Ввести номер вручную' и отправить номер в формате +71234567890.",
        reply_markup=kb
    )
    await state.set_state(LeadForm.contact)

# --- Контакт ---
@dp.message(LeadForm.contact)
async def ask_age(message: types.Message, state: FSMContext):
    # Accept either a shared contact (message.contact) or a manually typed phone number (message.text)
    phone = None
    if message.contact and getattr(message.contact, 'phone_number', None):
        phone = message.contact.phone_number
    else:
        text = (message.text or "").strip()
        # If user pressed one of the helper buttons, give further instructions
        if text in ["Отправить контакт (через скрепку)", "Ввести номер вручную"]:
            await message.answer(
                "Чтобы отправить контакт:\n"
                "1) Нажмите на значок 'скрепка' -> 'Контакт' и выберите свой контакт;\n"
                "или\n"
                "2) Введите номер вручную в формате +71234567890 и отправьте.")
            return
        # basic validation: allow digits, +, spaces, parentheses and dashes
        if text:
            phone = text

    if not phone:
        await message.answer("Не удалось получить номер. Пожалуйста, отправьте контакт через скрепку или введите номер вручную.")
        return

    # Normalize and validate phone number: keep digits and leading +
        # --- Проверка и нормализация номера ---
    import re
    raw = phone.strip()
    normalized = re.sub(r"[\s()\-]", "", raw)  # убираем пробелы, скобки и дефисы

    # Автоисправление частых случаев
    fixed = None
    if re.fullmatch(r"7\d{10}", normalized):
        fixed = f"+{normalized}"
    elif re.fullmatch(r"9\d{9}", normalized):
        fixed = f"+7{normalized}"
    elif re.fullmatch(r"89\d{9}", normalized):
        fixed = normalized  # нормальный вид
    elif re.fullmatch(r"\+79\d{9}", normalized):
        fixed = normalized  # тоже нормальный вид
    elif re.fullmatch(r"8\d{10}", normalized):
        fixed = normalized
    elif re.fullmatch(r"\+7\d{10}", normalized):
        fixed = normalized

    if fixed:
        # всё ок, сохраняем
        await state.update_data(phone=fixed)

        # дружелюбное сообщение, если бот подправил номер
        if fixed != normalized:
            await message.answer(
                f"📱 Я немного подправил ваш номер, чтобы он был в нужном формате:\n"
                f"<b>{fixed}</b>",
                parse_mode="HTML"
            )
    else:
        # если номер не подходит ни под одно правило
        await message.answer(
            "⚠️ Пожалуйста, введите корректный номер телефона:\n"
            "• в формате +7XXXXXXXXXX\n"
            "или\n"
            "• в формате 8XXXXXXXXXX\n\n"
            "Пример: +79151234567 или 89261234567"
        )
        return

    await state.update_data(phone=normalized)
    await message.answer(
        "Сколько лет ребенку?",
        reply_markup=types.ReplyKeyboardRemove()  # Убираем клавиатуру для ввода числа
    )
    await state.set_state(LeadForm.age)

# --- Возраст ---
@dp.message(LeadForm.age)
async def ask_mshp_status(message: types.Message, state: FSMContext):
    # Validate age: must be a positive integer
    try:
        age = int(message.text.strip())
        if age <= 0 or age > 18:  # Добавим разумные ограничения
            raise ValueError("Age out of range")
    except ValueError:
        await message.answer("Пожалуйста, введите корректный возраст (целое число от 1 до 18).")
        return

    await state.update_data(age=age)
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Да")],
            [KeyboardButton(text="Еще нет")]
        ],
        resize_keyboard=True
    )
    await message.answer("Ребенок учится в МШП?", reply_markup=kb)
    await state.set_state(LeadForm.is_mshp_student)

# --- Статус обучения в МШП ---
@dp.message(LeadForm.is_mshp_student)
async def ask_time(message: types.Message, state: FSMContext):
    # Accept only "Да" or "Еще нет"
    status = message.text.strip()
    if status not in ["Да", "Еще нет"]:
        await message.answer('Пожалуйста, выберите "Да" или "Еще нет" с помощью кнопок.')
        return

    await state.update_data(is_mshp_student=status)
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="13:00 - 14:00")],
            [KeyboardButton(text="14:30 - 15:30")],
            [KeyboardButton(text="16:00 - 17:00")]
        ],
        resize_keyboard=True
    )
    await message.answer("На какое время вы хотите записаться на мастер-класс?", reply_markup=kb)
    await state.set_state(LeadForm.time)

# --- Финальный шаг: выбор времени ---
@dp.message(LeadForm.time)
async def finish_registration(message: types.Message, state: FSMContext):
    # Accept only predefined time buttons
    allowed_times = {"13:00 - 14:00", "14:30 - 15:30", "16:00 - 17:00"}
    chosen = (message.text or "").strip()
    if chosen not in allowed_times:
        await message.answer("Пожалуйста, выберите время с помощью кнопок: 13:00 - 14:00, 14:30 - 15:30 или 16:00 - 17:00.")
        return

    await state.update_data(time=chosen)
    data = await state.get_data()
    
    # Сохранение в Google Sheets
    if sheet is not None:
        try:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sheet.append_row(
                [
                    data.get('name', ''),
                    data.get('phone', ''),
                    str(data.get('age', '')),  # Преобразуем в строку для надежности
                    data.get('is_mshp_student', ''),
                    data.get('time', ''),
                    timestamp
                ],
                value_input_option='USER_ENTERED'
            )
            logger.info(f"Successfully saved data for user {data.get('name', '')}")
        except Exception as e:
            logger.exception("Failed to append row to Google Sheets")
            await message.answer("Регистрация принята, но произошла ошибка при сохранении данных.")
            return

    text = (
    f"Спасибо за регистрацию, <b>{data.get('name', '')}</b>! 🎉<br>"
    f"🕒 Ждём вас на мастер-классе в <b>{data.get('time', '')}</b>!"
)
    await message.answer(text, parse_mode="HTML", reply_markup=types.ReplyKeyboardRemove())

    await message.answer(text, reply_markup=types.ReplyKeyboardRemove())
    await state.clear()

# --- Запуск ---
async def main():
    logger.info("Starting bot...")
    await set_commands(bot)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.exception("Bot stopped due to an error")