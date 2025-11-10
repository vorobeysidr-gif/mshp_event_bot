from aiogram import Router, types # type: ignore
from aiogram.fsm.context import FSMContext # pyright: ignore[reportMissingImports]
from services.sheets import append_lead_row
from services.backup import backup_to_csv
import logging

router = Router()
logger = logging.getLogger(__name__)

# --- Финальный шаг: завершение регистрации ---
@router.message()
async def finish_registration(message: types.Message, state: FSMContext):
    data = await state.get_data()

    # --- Сохранение данных ---
    try:
        append_lead_row(data)
        logger.info(f"✅ Saved to Google Sheets: {data.get('name', '')}")
    except Exception as e:
        backup_to_csv(data)
        logger.warning(f"⚠️ Saved to backup.csv (Google Sheets failed): {e}")

    # --- Текст финального сообщения ---
    text = (
        f"<b>Спасибо за регистрацию, {data.get('name', '')}!</b> 🎉\n\n"
        f"🕒 Ждём вас на мастер-классе:\n"
        f"<b>{data.get('time', '')}</b>\n\n"
        f"До встречи! 🌟"
    )

    # --- Отправка пользователю ---
    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=types.ReplyKeyboardRemove()
    )

    await state.clear()
