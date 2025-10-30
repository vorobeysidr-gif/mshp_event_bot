import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from config import BOT_TOKEN
from handlers import registration
async def set_commands(bot: Bot) -> None:
    commands = [
        BotCommand(command="start", description="Начать запись на мастер-класс"),
    ]
    await bot.set_my_commands(commands)
async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not set in environment")
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    # Подключаем только рабочий роутер регистрации
    dp.include_router(registration.router)
    await set_commands(bot)
    logging.info("Bot started successfully")
    await dp.start_polling(bot)
if __name__ == "__main__":
    asyncio.run(main())