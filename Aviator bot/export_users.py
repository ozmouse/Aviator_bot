from aiogram import Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database import get_all_users
from config import CHAT_ID
from keyboards import get_admin_menu
from utils import in_chat

def register_export_handlers(dp: Dispatcher, bot):
    @dp.callback_query(lambda c: c.data == "export_users")
    async def export_users(callback: types.CallbackQuery):
        if not in_chat(callback):
            await callback.answer("Доступно только в чате операторов!")
            return
        users = get_all_users()
        if not users:
            await callback.message.edit_text("📋 В базе нет пользователей.", reply_markup=get_admin_menu())
            await callback.answer()
            return
        
        user_list = "\n".join(
            f"ID: <code>{user[0]}</code>, Username: @{user[1] or 'None'}, Phone: {user[2]}, Country: {user[3]}, Time: {user[4]}"
            for user in users
        )
        
        await bot.send_message(
            chat_id=CHAT_ID,
            text=f"📊 Список пользователей:\n{user_list}",
            parse_mode="HTML"
        )
        await callback.message.edit_text("📊 Файл готов", reply_markup=get_admin_menu())
        await callback.answer()