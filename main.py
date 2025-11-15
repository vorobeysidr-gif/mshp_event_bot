import logging
import os
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher
from aiogram.types import Update
from config import BOT_TOKEN, HOST
from handlers import agreement, registration

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"https://{HOST}{WEBHOOK_PATH}"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Подключаем роутеры
dp.include_router(agreement.router)
dp.include_router(registration.router)

app = FastAPI()


@app.on_event("startup")
async def on_startup():
    if os.getenv("UVICORN_WORKER_NAME") == "uvicorn-worker-1":
        logger.info("Устанавливаю webhook...")
        await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)
        logger.info("Webhook установлен: %s", WEBHOOK_URL)


@app.on_event("shutdown")
async def on_shutdown():
    if os.getenv("UVICORN_WORKER_NAME") == "uvicorn-worker-1":
        logger.info("Удаляю webhook...")
        await bot.delete_webhook()
        logger.info("Webhook удалён")
        await bot.session.close()


@app.post(WEBHOOK_PATH)
async def telegram_webhook(request: Request):
    update = Update.model_validate(await request.json())
    await dp.feed_update(bot, update)
    return {"ok": True}
