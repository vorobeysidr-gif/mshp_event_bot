import logging
import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.types.bot_command import BotCommand
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from config import BOT_TOKEN, HOST
from handlers import agreement, registration
import uvicorn


WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"https://{HOST}{WEBHOOK_PATH}"
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = 8080


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def on_startup(bot: Bot):
    logger.info("Настройка webhook...")
    await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)
    logger.info(f"Webhook установлен: {WEBHOOK_URL}")


async def on_shutdown(bot: Bot):
    logger.info("Удаляем webhook...")
    await bot.delete_webhook()
    logger.info("Webhook удалён")


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Роутеры (handlers)
dp.include_router(agreement.router)
dp.include_router(registration.router)

# Приложение aiohttp
app = web.Application()
SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
setup_application(app, dp, bot=bot)

dp.startup.register(on_startup)
dp.shutdown.register(on_shutdown)

logging.info("Бот запущен в режиме webhook через Uvicorn")


async def set_commands(bot: Bot) -> None:
    commands = [
        BotCommand(command="start", description="Начать запись на мастер-класс")
    ]
    await bot.set_my_commands(commands)



if __name__ == "__main__":
    uvicorn.run(
        "main:main",
        factory=True,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
        log_level="info",
        reload=True 
    )