import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from handlers import agreement, registration, finish

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

async def main():
    # Регистрация хендлеров
    dp.include_router(agreement.router)
    dp.include_router(registration.router)
    dp.include_router(finish.router)

    logging.info("Bot started successfully 🚀")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
