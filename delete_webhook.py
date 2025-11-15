import asyncio
from aiogram import Bot
from config import BOT_TOKEN


async def delete_webhook():
    """Удаляет webhook и проверяет статус"""
    bot = Bot(token=BOT_TOKEN)
    try:
        # Удаляем webhook и все ожидающие обновления
        result = await bot.delete_webhook(drop_pending_updates=True)
        print(f"✅ Webhook удален: {result}")
        
        # Проверяем текущий статус webhook
        webhook_info = await bot.get_webhook_info()
        print(f"\n📊 Информация о webhook:")
        print(f"  URL: {webhook_info.url if webhook_info.url else '(не установлен)'}")
        print(f"  Ожидающих обновлений: {webhook_info.pending_update_count}")
        
        if not webhook_info.url:
            print("\n✅ Бот готов к работе в режиме polling!")
        else:
            print(f"\n⚠️ Webhook все еще активен: {webhook_info.url}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(delete_webhook())
