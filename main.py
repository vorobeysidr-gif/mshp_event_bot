import logging
import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.types.bot_command import BotCommand
from config import BOT_TOKEN, HOST
from handlers import agreement, registration

WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"https://{HOST}{WEBHOOK_PATH}"


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


async def set_commands(bot: Bot) -> None:
    commands = [
        BotCommand(command="start", description="Начать запись на мастер-класс")
    ]
    await bot.set_my_commands(commands)


async def create_app():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(agreement.router)
    dp.include_router(registration.router)

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    app = web.Application()
    app["bot"] = bot
    dp.workflow_data.update(app=app)

    async def on_start(_):
        asyncio.create_task(dp.start_polling(bot))

    app.on_startup.append(on_start)
    app.on_cleanup.append(lambda _: asyncio.create_task(on_shutdown(bot)))

    return app


def app():
    return create_app()