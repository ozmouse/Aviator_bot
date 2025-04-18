import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = int(os.getenv("CHAT_ID"))
SECRET_PASSWORD = os.getenv("SECRET_PASSWORD")
TOTAL_DIR = "totals"

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

MESSAGES = {
    "enter_password": {"ru": "🔐 Введите пароль:"},
    "password_correct": {"ru": "✅ Пароль верный! Отправьте контакт:"},
    "password_incorrect": {"ru": "❌ Неверный пароль. Попробуйте снова."},
    "send_contact": {"ru": "🚫 Отправьте контакт через кнопку!"},
    "registration_complete": {"ru": "✅ Регистрация завершена!"},
    "already_registered": {"ru": "Вы уже зарегистрированы!"}
}

DEPOSIT_TEXTS = {
    "ru": {"deposit": "Пожалуйста, внесите депозит для начала работы."}
}