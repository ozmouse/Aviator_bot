import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from admin_bot import register_admin_handlers
from user_bot import register_user_handlers

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    try:
        bot = Bot(token=BOT_TOKEN)
        dp = Dispatcher()
        register_admin_handlers(dp, bot)
        register_user_handlers(dp, bot)
        logger.info("Бот запущен, начинаем polling")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())