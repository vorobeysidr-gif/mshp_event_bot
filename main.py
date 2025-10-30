import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from config import BOT_TOKEN
from handlers import registration
from handlers import agreement
async def set_commands(bot: Bot) -> None:
    commands = [
        BotCommand(command="start", description="Начать запись на мастер-класс"),
        BotCommand(command="version", description="Проверить версию бота"),
    ]
    await bot.set_my_commands(commands)
async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not set in environment")
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    # Подключаем роутеры: сначала согласие, затем регистрация
    dp.include_router(agreement.router)
    dp.include_router(registration.router)
    await set_commands(bot)
    logging.info("Bot started successfully")
    try:
        await dp.start_polling(bot)
    except (KeyboardInterrupt, asyncio.CancelledError):
        logging.info("Bot stopped by user (graceful shutdown)")
    finally:
        await bot.session.close()
if __name__ == "__main__":
    asyncio.run(main())