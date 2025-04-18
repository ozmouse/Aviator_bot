import asyncio
import random
from aiogram.types import Message

async def loading_animation(message: Message):
    """Анимация загрузки перед логами (одно сообщение)"""
    stages = [
        "🔍 Checking number...",
        "📡 Connecting to Telegram...",
        "🌍 Connecting to servers...",
        "🛡️ Confirming access..."
    ]

    loading_msg = await message.answer("<pre>⏳ Starting process...</pre>", parse_mode="HTML")

    for stage in stages:
        try:
            await asyncio.sleep(2)
            await loading_msg.edit_text(f"<pre>{stage}</pre>", parse_mode="HTML")
        except Exception as e:
            await message.answer(f"Error: {str(e)}")
            break

    await asyncio.sleep(1)
    await loading_msg.delete()

async def fake_console_logs(message: Message):
    """Выводит консольные логи + внизу анимацию загрузки (%)"""
    logs = [
        "[INFO] Connecting to VPN server...",
        "[INFO] Establishing secure connection...",
        "[INFO] Checking IP address...",
        "[INFO] Searching for network...",
        "[INFO] Retrieving country info...",
        "[INFO] Analyzing phone number...",
        "[SECURITY] Checking for threats...",
        "[SECURITY] Encrypting data...",
        "[SECURITY] Generating security key...",
        "[DATA] Sending request to Telegram API...",
        "[DATA] Receiving response from servers...",
        "[SECURITY] Authenticating identity...",
        "[LOG] Writing data to security log...",
        "[INFO] Decoding response...",
        "[INFO] Analyzing user data...",
        "[SECURITY] Performing double security check...",
        "[SECURITY] Bypassing security systems...",
        "[DATA] Optimizing connection...",
        "[INFO] Checking connection speed...",
        "[LOG] Notifying Telegram server...",
        "[SECURITY] Validating data...",
        "[INFO] Analyzing packet headers...",
        "[SECURITY] Issuing temporary token...",
        "[LOG] Logging connection time...",
        "[DATA] Requesting user confirmation...",
        "[SECURITY] Analyzing suspicious activity...",
        "[INFO] Intercepting connection headers...",
        "[SECURITY] Connecting via secure channel...",
        "[INFO] Filtering spam...",
        "[DATA] Downloading data from server...",
        "[SECURITY] Final security check...",
        "[INFO] Final stage of synchronization...",
        "[SECURITY] Last key check...",
        "[INFO] Preparing for operation completion...",
        "[SUCCESS] Access granted!",
        "[SUCCESS] Synchronization successful!"
    ]

    log_text = "<pre>[SYSTEM] Starting process...</pre>"
    log_message = await message.answer(log_text, parse_mode="HTML")

    # Создаем сообщение для анимации загрузки
    loading_msg = await message.answer("<pre>⏳ Loading... 0%</pre>", parse_mode="HTML")

    for i, log in enumerate(logs):
        try:
            await asyncio.sleep(random.randint(1, 3))
            log_text += f"\n{log}"
            await log_message.edit_text(f"<pre>{log_text}</pre>", parse_mode="HTML")

            # Обновляем анимацию загрузки внизу
            progress = (i + 1) * 100 // len(logs)  # Вычисляем процент
            await loading_msg.edit_text(f"<pre>⏳ Loading... {progress}%</pre>", parse_mode="HTML")
        except Exception as e:
            await message.answer(f"Error during log processing: {str(e)}")
            break

    await asyncio.sleep(1)
    await loading_msg.edit_text("<pre>✅ Loading complete!</pre>", parse_mode="HTML")

    # Удаляем логи через 5 секунд, оставляя только "Loading complete!"
    await asyncio.sleep(5)
    await log_message.delete()
