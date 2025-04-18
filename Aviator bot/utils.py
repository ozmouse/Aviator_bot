import logging

logger = logging.getLogger(__name__)

def in_chat(chat_id: int, allowed_chat_id: str) -> bool:
    result = str(chat_id) == str(allowed_chat_id)
    logger.debug(f"Checking chat: chat_id={chat_id}, allowed_chat_id={allowed_chat_id}, result={result}")
    return result