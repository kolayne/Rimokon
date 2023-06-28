from io import BytesIO
from typing import Optional

from PIL import ImageGrab
import telebot

from .plugin_helpers import help_description


__all__ = ['screen', 'screenf']


def take_screenshot_or_complain_to(bot: telebot.TeleBot, message: telebot.types.Message) -> Optional[BytesIO]:
    try:
        screenshot = ImageGrab.grab()
    except OSError as e:
        bot.reply_to(message, f"Error: your machine doesn't seem to support this:\n{e}")
        return
    img = BytesIO()
    img.name = 'i.png'  # Telegram doesn't like untitled files
    screenshot.save(img, 'PNG')
    img.seek(0)
    return img

@help_description("Take a screenshot and send as a photo")
def screen(bot: telebot.TeleBot, message: telebot.types.Message, _: str) -> None:
    img = take_screenshot_or_complain_to(bot, message)
    if img:
        bot.send_photo(message.chat.id, img, reply_to_message_id=message.message_id)

@help_description("Take a screenshot and send as a document")
def screenf(bot: telebot.TeleBot, message: telebot.types.Message, _: str) -> None:
    img = take_screenshot_or_complain_to(bot, message)
    if img:
        bot.send_document(message.chat.id, img, reply_to_message_id=message.message_id)
