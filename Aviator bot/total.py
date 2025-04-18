import os
import random
import logging
from aiogram import types
from database import get_total_message
from config import TOTAL_DIR

logger = logging.getLogger(__name__)

async def send_total(bot, user_id, gif_path):
    try:
        if not gif_path or not os.path.exists(gif_path):
            logger.error(f"GIF не найден: {gif_path}")
            return False

        message_text = get_total_message(user_id)
        if not message_text:
            logger.warning(f"Нет сообщения для user_id={user_id}")
            message_text = "Ваш тотал готов!"

        with open(gif_path, "rb") as gif:
            await bot.send_animation(
                chat_id=user_id,
                animation=gif,
                caption=f"||{message_text}||",
                parse_mode="MarkdownV2"
            )
        logger.info(f"Тотал успешно отправлен пользователю user_id={user_id}")
        return True

    except FileNotFoundError as e:
        logger.error(f"Файл не найден: {gif_path}, ошибка: {e}")
        return False
    except Exception as e:
        logger.error(f"Ошибка отправки тотала пользователю user_id={user_id}: {e}")
        return False

def get_random_total_gif():
    try:
        if not os.path.exists(TOTAL_DIR):
            logger.error(f"Папка {TOTAL_DIR} не найдена")
            return None

        gif_files = [f for f in os.listdir(TOTAL_DIR) if f.endswith((".gif", ".mp4"))]
        if not gif_files:
            logger.error(f"Нет GIF или MP4 в папке {TOTAL_DIR}")
            return None

        gif_path = os.path.join(TOTAL_DIR, random.choice(gif_files))
        logger.debug(f"Выбран GIF: {gif_path}")
        return gif_path

    except Exception as e:
        logger.error(f"Ошибка получения случайного GIF: {e}")
        return None