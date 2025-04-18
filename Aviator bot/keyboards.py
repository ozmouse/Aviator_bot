from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_admin_menu() -> InlineKeyboardMarkup:
    """
    Возвращает инлайн-клавиатуру для админ-панели.
    
    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопками для админских функций.
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 Отправить тотал", callback_data="send_total")],
        [InlineKeyboardButton(text="📦 Отправить серию", callback_data="send_total_series")],
        [InlineKeyboardButton(text="⚠️ Отправить ошибку", callback_data="send_error")],
        [InlineKeyboardButton(text="📊 Получить всех пользователей", callback_data="get_all_users")],
        [InlineKeyboardButton(text="🌍 Рассылка", callback_data="broadcast")]
    ])
    return keyboard