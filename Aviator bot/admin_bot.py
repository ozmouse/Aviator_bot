import os
import asyncio
import random
import logging
import svgwrite
from aiogram import Dispatcher, Bot, types
from aiogram.filters import Command, CommandStart, BaseFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import FSInputFile, BotCommand, BufferedInputFile
from config import CHAT_ID, TOTAL_DIR
from database import get_user, get_all_users, get_all_countries, get_users_by_country
from user_bot import load_language_messages, get_user_language

logger = logging.getLogger(__name__)

# Фильтр для проверки админского чата
class AdminChatFilter(BaseFilter):
    async def __call__(self, obj: types.Message) -> bool:
        try:
            chat_id = obj.chat.id
            is_admin_chat = str(chat_id) == str(CHAT_ID)
            logger.debug(f"AdminChatFilter: chat_id={chat_id}, CHAT_ID={CHAT_ID}, is_admin_chat={is_admin_chat}")
            return is_admin_chat
        except Exception as e:
            logger.error(f"Ошибка в AdminChatFilter: {e}", exc_info=True)
            return False

# Определение состояний FSM (только для рассылки)
class AdminStates(StatesGroup):
    awaiting_broadcast_message = State()
    awaiting_broadcast_media = State()

# Валидация идентификатора пользователя
async def validate_identifier(identifier: str) -> tuple[int, tuple] | tuple[None, None]:
    """Валидирует user_id или username, возвращает user_id и user_data."""
    try:
        identifier = identifier.strip()
        if not identifier:
            logger.debug("Пустой идентификатор")
            return None, None
        user_data = None
        if identifier.startswith('@'):
            username = identifier[1:]
            user_data = await get_user_by_username(username)
            logger.debug(f"Поиск по username: {username}, результат={user_data}")
        else:
            try:
                user_id = int(identifier)
                if user_id <= 0:
                    logger.debug(f"ID должен быть положительным: {identifier}")
                    return None, None
                user_data = get_user(user_id)
                logger.debug(f"Поиск по user_id: {user_id}, результат={user_data}")
            except ValueError:
                logger.debug(f"Некорректный user_id: {identifier}")
                return None, None
        if not user_data:
            logger.debug(f"Пользователь не найден для идентификатора: {identifier}")
            return None, None
        user_id = int(user_data[0])
        return user_id, user_data
    except Exception as e:
        logger.error(f"Ошибка в validate_identifier для identifier={identifier}: {e}", exc_info=True)
        return None, None

# Функция отправки тотала
async def send_total(bot: Bot, user_id: int, gif_path: str) -> bool:
    """Отправляет одиночный тотал пользователю под спойлером."""
    logger.info(f"Попытка отправки тотала: user_id={user_id}, gif_path={gif_path}")
    try:
        if not gif_path or not os.path.exists(gif_path):
            logger.error(f"GIF не найден: {gif_path}")
            return False

        user = get_user(user_id)
        if not user:
            logger.error(f"Пользователь {user_id} не найден")
            return False

        country = user[3] or "Unknown"
        lang_code = get_user_language(country)
        messages = load_language_messages(lang_code)
        message_text = random.choice(messages["total"]) or "Ваш тотал готов!"

        def escape_markdown_v2(text: str) -> str:
            chars = r'_[]()~`>#+-=|{}.!'
            for char in chars:
                text = text.replace(char, f'\\{char}')
            return text

        message_text = escape_markdown_v2(message_text)
        with open(gif_path, 'rb') as file:
            animation = BufferedInputFile(file.read(), filename=os.path.basename(gif_path))
        await bot.send_animation(
            chat_id=user_id,
            animation=animation,
            caption=f"||{message_text}||",
            parse_mode="MarkdownV2",
            has_spoiler=True
        )
        logger.info(f"Тотал успешно отправлен пользователю user_id={user_id}")
        return True
    except aiogram.exceptions.TelegramForbiddenError:
        logger.warning(f"Пользователь {user_id} заблокировал бота")
        return False
    except aiogram.exceptions.TelegramRetryAfter as e:
        logger.warning(f"Лимит Telegram, ожидание {e.retry_after} секунд")
        await asyncio.sleep(e.retry_after)
        return await send_total(bot, user_id, gif_path)
    except Exception as e:
        logger.error(f"Ошибка отправки тотала пользователю user_id={user_id}: {e}", exc_info=True)
        return False

# Получение случайного GIF
def get_random_total_gif() -> str | None:
    """Возвращает путь к случайному GIF."""
    try:
        if not os.path.exists(TOTAL_DIR):
            logger.error(f"Папка {TOTAL_DIR} не найдена")
            return None

        gif_files = [f for f in os.listdir(TOTAL_DIR) if f.lower().endswith((".gif", ".mp4"))]
        if not gif_files:
            logger.error(f"Нет GIF или MP4 в папке {TOTAL_DIR}")
            return None

        gif_path = os.path.join(TOTAL_DIR, random.choice(gif_files))
        logger.debug(f"Выбран GIF: {gif_path}")
        return gif_path
    except Exception as e:
        logger.error(f"Ошибка получения случайного GIF: {e}", exc_info=True)
        return None

# Функция отправки ошибки
async def send_error(bot: Bot, user_id: int) -> bool:
    """Отправляет сообщение об ошибке пользователю."""
    logger.info(f"Попытка отправки ошибки: user_id={user_id}")
    try:
        user = get_user(user_id)
        if not user:
            logger.error(f"Пользователь {user_id} не найден")
            return False

        country = user[3] or "Unknown"
        lang_code = get_user_language(country)
        messages = load_language_messages(lang_code)
        message_text = random.choice(messages["error"]) or "Произошла ошибка. Попробуйте позже."
        await bot.send_message(user_id, message_text)
        logger.info(f"Ошибка отправлена user_id={user_id}")
        return True
    except aiogram.exceptions.TelegramForbiddenError:
        logger.warning(f"Пользователь {user_id} заблокировал бота")
        return False
    except aiogram.exceptions.TelegramRetryAfter as e:
        logger.warning(f"Лимит Telegram, ожидание {e.retry_after} секунд")
        await asyncio.sleep(e.retry_after)
        return await send_error(bot, user_id)
    except Exception as e:
        logger.error(f"Ошибка отправки ошибки user_id={user_id}: {e}", exc_info=True)
        return False

# Функция отправки серии тоталов
async def send_total_series(bot: Bot, user_id: int, delay: int = 60, count: int = 10):
    """Отправляет серию из 10 тоталов пользователю с интервалом в 1 минуту."""
    logger.info(f"Запуск серии из {count} тоталов с интервалом {delay}с для user_id={user_id}")
    try:
        for i in range(count):
            gif_path = get_random_total_gif()
            if not gif_path:
                logger.warning(f"Нет GIF для тотала {i+1}/{count}, user_id={user_id}")
                continue
            success = await send_total(bot, user_id, gif_path)
            if success:
                logger.info(f"Тотал {i+1}/{count} отправлен, user_id={user_id}")
            else:
                logger.error(f"Ошибка тотала {i+1}/{count}, user_id={user_id}")
            if i < count - 1:  # Не ждем после последнего тотала
                await asyncio.sleep(delay)
    except Exception as e:
        logger.error(f"Ошибка серии, user_id={user_id}: {e}", exc_info=True)

# Генерация SVG с пользователями
def generate_users_svg(users: list) -> str | None:
    """Генерирует SVG-файл с данными пользователей."""
    try:
        dwg = svgwrite.Drawing("users.svg", profile="tiny", size=("800px", f"{len(users) * 30 + 50}px"))
        dwg.add(dwg.rect(insert=(0, 0), size=("100%", "100%"), fill="white"))
        dwg.add(dwg.text("Users List", insert=(10, 20), font_size="16", font_family="Arial", fill="black"))

        for i, user in enumerate(users):
            telegram_id, username, phone, country = user
            text = f"ID: {telegram_id}, Username: @{username or 'None'}, Country: {country or 'N/A'}"
            dwg.add(dwg.text(text, insert=(10, 40 + i * 30), font_size="14", font_family="Arial", fill="black"))

        dwg.save()
        logger.info("SVG-файл сгенерирован: users.svg")
        return "users.svg"
    except Exception as e:
        logger.error(f"Ошибка генерации SVG: {e}", exc_info=True)
        return None

# Поиск пользователя по username
async def get_user_by_username(username: str) -> tuple | None:
    """Ищет пользователя по username в базе данных."""
    try:
        users = get_all_users()
        for user in users:
            telegram_id, user_username, phone, country = user
            if user_username and user_username.lower() == username.lower():
                logger.debug(f"Найден пользователь: telegram_id={telegram_id}, username={user_username}")
                return user
        logger.debug(f"Пользователь не найден для username={username}")
        return None
    except Exception as e:
        logger.error(f"Ошибка в get_user_by_username для username={username}: {e}", exc_info=True)
        return None

# Регистрация админских обработчиков
def register_admin_handlers(dp: Dispatcher, bot: Bot):
    logger.info("Регистрация админских обработчиков")

    # Установка команд для автозаполнения
    async def set_bot_commands():
        commands = [
            BotCommand(command="hello", description="Открыть админ-панель"),
            BotCommand(command="help", description="Показать список команд"),
            BotCommand(command="send_total", description="Отправить тотал: /send_total <id/username>"),
            BotCommand(command="send_series", description="Отправить серию тоталов: /send_series <id/username>"),
            BotCommand(command="send_error", description="Отправить ошибку: /send_error <id/username>"),
            BotCommand(command="get_all_users", description="Получить список пользователей в SVG"),
            BotCommand(command="broadcast", description="Рассылка по стране: /broadcast <country>"),
            BotCommand(command="clean", description="Очистить все FSM-состояния"),
            BotCommand(command="start", description="Запустить бота (используйте /help)")
        ]
        await bot.set_my_commands(commands)
        logger.info("Команды бота установлены для автозаполнения")

    # Вызов установки команд при старте
    asyncio.create_task(set_bot_commands())

    # Команда /hello
    @dp.message(AdminChatFilter(), Command("hello"))
    async def cmd_hello(message: types.Message):
        try:
            await message.reply("📋 Добро пожаловать в админ-панель! Используйте /help для списка команд.")
        except Exception as e:
            logger.error(f"Ошибка в /hello: {e}", exc_info=True)
            await message.reply("❌ Ошибка. Обратитесь в поддержку.")

    # Команда /help
    @dp.message(AdminChatFilter(), Command("help"))
    async def cmd_help(message: types.Message):
        try:
            help_text = (
                "📋 Список команд админ-панели:\n\n"
                "/hello - Открыть админ-панель\n"
                "/help - Показать этот список\n"
                "/send_total <id/username> - Отправить одиночный тотал\n"
                "/send_series <id/username> - Отправить серию тоталов (10 штук)\n"
                "/send_error <id/username> - Отправить сообщение об ошибке\n"
                "/get_all_users - Получить список пользователей в SVG\n"
                "/broadcast <country> - Запустить рассылку по стране\n"
                "/clean - Очистить все FSM-состояния"
            )
            await message.reply(help_text)
        except Exception as e:
            logger.error(f"Ошибка в /help: {e}", exc_info=True)
            await message.reply("❌ Ошибка. Обратитесь в поддержку.")

    # Команда /start
    @dp.message(AdminChatFilter(), CommandStart())
    async def cmd_start_admin(message: types.Message):
        try:
            await message.reply("❌ Используйте /help для списка команд.")
        except Exception as e:
            logger.error(f"Ошибка в /start: {e}", exc_info=True)
            await message.reply("❌ Ошибка. Обратитесь в поддержку.")

    # Команда /clean
    @dp.message(AdminChatFilter(), Command("clean"))
    async def cmd_clean(message: types.Message, state: FSMContext):
        try:
            await state.clear()
            await message.reply("✅ Все FSM-состояния очищены.")
            logger.info("FSM-состояния очищены по команде /clean")
        except Exception as e:
            logger.error(f"Ошибка в /clean: {e}", exc_info=True)
            await message.reply("❌ Ошибка. Обратитесь в поддержку.")

    # Команда /send_total
    @dp.message(AdminChatFilter(), Command("send_total"))
    async def cmd_send_total(message: types.Message):
        try:
            args = message.text.split(maxsplit=1)
            if len(args) < 2:
                await message.reply("❌ Укажите ID или username: /send_total <id/username>")
                return
            identifier = args[1].strip()
            user_id, user_data = await validate_identifier(identifier)
            if not user_data:
                await message.reply("❌ Пользователь не найден или некорректный ID/username.")
                return

            gif_path = get_random_total_gif()
            if not gif_path:
                await message.reply("❌ Нет доступных GIF.")
                return

            success = await send_total(bot, user_id, gif_path)
            if success:
                await message.reply(f"✅ Тотал отправлен пользователю <code>{user_id}</code>", parse_mode="HTML")
                await bot.send_message(
                    CHAT_ID,
                    f"📤 Тотал отправлен пользователю <code>{user_id}</code>",
                    parse_mode="HTML"
                )
            else:
                await message.reply(f"❌ Ошибка отправки тотала <code>{user_id}</code>", parse_mode="HTML")
        except Exception as e:
            logger.error(f"Ошибка в /send_total: {e}", exc_info=True)
            await message.reply("❌ Ошибка. Попробуйте снова.")

    # Команда /send_series
    @dp.message(AdminChatFilter(), Command("send_series"))
    async def cmd_send_series(message: types.Message):
        try:
            args = message.text.split(maxsplit=1)
            if len(args) < 2:
                await message.reply("❌ Укажите ID или username: /send_series <id/username>")
                return
            identifier = args[1].strip()
            user_id, user_data = await validate_identifier(identifier)
            if not user_data:
                await message.reply("❌ Пользователь не найден или некорректный ID/username.")
                return

            await message.reply(f"✅ Серия запланирована для <code>{user_id}</code>", parse_mode="HTML")
            await bot.send_message(CHAT_ID, f"📦 Серия тоталов запланирована для <code>{user_id}</code>", parse_mode="HTML")
            asyncio.create_task(send_total_series(bot, user_id))
        except Exception as e:
            logger.error(f"Ошибка в /send_series: {e}", exc_info=True)
            await message.reply("❌ Ошибка. Попробуйте снова.")

    # Команда /send_error
    @dp.message(AdminChatFilter(), Command("send_error"))
    async def cmd_send_error(message: types.Message):
        try:
            args = message.text.split(maxsplit=1)
            if len(args) < 2:
                await message.reply("❌ Укажите ID или username: /send_error <id/username>")
                return
            identifier = args[1].strip()
            user_id, user_data = await validate_identifier(identifier)
            if not user_data:
                await message.reply("❌ Пользователь не найден или некорректный ID/username.")
                return

            success = await send_error(bot, user_id)
            if success:
                await message.reply(f"✅ Ошибка отправлена пользователю <code>{user_id}</code>", parse_mode="HTML")
                await bot.send_message(
                    CHAT_ID,
                    f"⚠️ Ошибка отправлена пользователю <code>{user_id}</code>",
                    parse_mode="HTML"
                )
            else:
                await message.reply(f"❌ Ошибка отправки <code>{user_id}</code>", parse_mode="HTML")
        except Exception as e:
            logger.error(f"Ошибка в /send_error: {e}", exc_info=True)
            await message.reply("❌ Ошибка. Попробуйте снова.")

    # Команда /get_all_users
    @dp.message(AdminChatFilter(), Command("get_all_users"))
    async def cmd_get_all_users(message: types.Message):
        try:
            users = get_all_users()
            if not users:
                await message.reply("🚫 Нет пользователей.")
                return
            svg_file = generate_users_svg(users)
            if not svg_file:
                await message.reply("❌ Ошибка генерации SVG.")
                return
            await bot.send_document(
                CHAT_ID,
                document=FSInputFile(path=svg_file, filename="users.svg"),
                caption="📊 Список пользователей"
            )
            await message.reply("✅ SVG-файл отправлен.")
        except Exception as e:
            logger.error(f"Ошибка в /get_all_users: {e}", exc_info=True)
            await message.reply("❌ Ошибка. Обратитесь в поддержку.")

    # Команда /broadcast
    @dp.message(AdminChatFilter(), Command("broadcast"))
    async def start_broadcast(message: types.Message, state: FSMContext):
        try:
            args = message.text.split(maxsplit=1)
            if len(args) < 2:
                countries = get_all_countries()
                countries_text = "\n".join([f"- {c}" for c in countries]) if countries else "Нет стран."
                await message.reply(f"❌ Укажите страну: /broadcast <country>\nДоступные страны:\n{countries_text}")
                return
            country = args[1].strip()
            countries = get_all_countries()
            if country not in countries:
                countries_text = "\n".join([f"- {c}" for c in countries]) if countries else "Нет стран."
                await message.reply(f"❌ Страна не найдена. Доступные страны:\n{countries_text}")
                return
            await state.update_data(country=country)
            await state.set_state(AdminStates.awaiting_broadcast_message)
            await message.reply(f"📝 Введите сообщение для рассылки в {country}:")
            logger.debug(f"FSM: Установлено состояние awaiting_broadcast_message, country={country}")
        except Exception as e:
            logger.error(f"Ошибка в /broadcast: {e}", exc_info=True)
            await message.reply("❌ Ошибка. Попробуйте снова.")
            await state.clear()

    @dp.message(AdminChatFilter(), AdminStates.awaiting_broadcast_message)
    async def process_broadcast_message(message: types.Message, state: FSMContext):
        try:
            broadcast_message = message.text.strip() if message.text else ""
            logger.debug(f"process_broadcast_message: message={broadcast_message}")
            if not broadcast_message:
                await message.reply("❌ Сообщение не может быть пустым.")
                return
            await state.update_data(message=broadcast_message)
            await state.set_state(AdminStates.awaiting_broadcast_media)
            await message.reply(
                f"🌍 Страна: {state.get_data().get('country')}\n\n📝 Сообщение:\n{broadcast_message}\n\n"
                "📸 Отправьте фото или видео (или напишите 'пропустить' для отправки без медиа):"
            )
            logger.debug(f"FSM: Установлено состояние awaiting_broadcast_media")
        except Exception as e:
            logger.error(f"Ошибка в process_broadcast_message: {e}", exc_info=True)
            await message.reply("❌ Ошибка. Попробуйте снова.")
            await state.clear()

    @dp.message(AdminChatFilter(), AdminStates.awaiting_broadcast_media)
    async def process_broadcast_media(message: types.Message, state: FSMContext):
        try:
            data = await state.get_data()
            logger.debug(f"process_broadcast_media: data={data}")
            media = None
            media_filename = None
            if message.photo:
                photo = message.photo[-1]
                file = await bot.get_file(photo.file_id)
                file_content = await bot.download_file(file.file_path)
                media_filename = f"photo_{photo.file_id}.jpg"
                media = {"type": "photo", "content": file_content.read(), "filename": media_filename}
                logger.debug(f"Получено фото: file_id={photo.file_id}, filename={media_filename}")
            elif message.video:
                video = message.video
                file = await bot.get_file(video.file_id)
                file_content = await bot.download_file(file.file_path)
                media_filename = f"video_{video.file_id}.mp4"
                media = {"type": "video", "content": file_content.read(), "filename": media_filename}
                logger.debug(f"Получено видео: file_id={video.file_id}, filename={media_filename}")
            elif message.text and message.text.strip().lower() == "пропустить":
                logger.debug("Медиа пропущено")
            else:
                await message.reply("❌ Отправьте фото, видео или напишите 'пропустить'.")
                return

            country = data.get("country")
            broadcast_message = data.get("message")
            user_ids = get_users_by_country(country)
            if not user_ids:
                await message.reply(f"🚫 Нет пользователей в стране {country}.")
                await state.clear()
                return

            success_count = 0
            for user_id in user_ids:
                try:
                    user = get_user(user_id)
                    if not user:
                        logger.warning(f"Пользователь {user_id} не найден при рассылке")
                        continue
                    user_country = user[3] or "Unknown"
                    lang_code = get_user_language(user_country)
                    messages = load_language_messages(lang_code)
                    localized_message = broadcast_message
                    if media:
                        media_file = BufferedInputFile(media["content"], filename=media["filename"])
                        if media["type"] == "photo":
                            await bot.send_photo(user_id, photo=media_file, caption=localized_message)
                        elif media["type"] == "video":
                            await bot.send_video(user_id, video=media_file, caption=localized_message)
                    else:
                        await bot.send_message(user_id, localized_message)
                    success_count += 1
                    await asyncio.sleep(0.05)
                except aiogram.exceptions.TelegramForbiddenError:
                    logger.warning(f"Пользователь {user_id} заблокировал бота при рассылке")
                    continue
                except aiogram.exceptions.TelegramRetryAfter as e:
                    logger.warning(f"Лимит Telegram, ожидание {e.retry_after} секунд")
                    await asyncio.sleep(e.retry_after)
                    continue
                except Exception as e:
                    logger.error(f"Ошибка отправки пользователю {user_id}: {e}", exc_info=True)
                    continue
            await message.reply(
                f"✅ Рассылка завершена в {country}: отправлено {success_count}/{len(user_ids)} сообщений."
            )
            await bot.send_message(
                CHAT_ID,
                f"🌍 Рассылка завершена в {country}: отправлено {success_count}/{len(user_ids)} сообщений."
            )
            await state.clear()
        except Exception as e:
            logger.error(f"Ошибка в process_broadcast_media: {e}", exc_info=True)
            await message.reply("❌ Ошибка. Попробуйте снова.")
            await state.clear()

    # Обработка любых текстовых сообщений
    @dp.message(AdminChatFilter())
    async def catch_unhandled_fsm_messages(message: types.Message, state: FSMContext):
        try:
            current_state = await state.get_state()
            logger.debug(f"catch_unhandled_fsm_messages: text='{message.text}', state={current_state}")
            if current_state == AdminStates.awaiting_broadcast_message:
                await process_broadcast_message(message, state)
                return
            elif current_state == AdminStates.awaiting_broadcast_media:
                await process_broadcast_media(message, state)
                return
            await message.reply("❌ Используйте /help для списка команд.")
            await state.clear()
        except Exception as e:
            logger.error(f"Ошибка в catch_unhandled_fsm_messages: {e}", exc_info=True)
            await message.reply("❌ Ошибка. Используйте /help.")
            await state.clear()

    logger.info("Все админские обработчики зарегистрированы")