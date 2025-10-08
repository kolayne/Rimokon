from io import BytesIO
from typing import Callable, IO, Optional

import telebot

from .plugin_helpers import help_description


__all__ = [
    'with_pil',
    'with_grim',
    'screen_as_photo_with',
    'screen_as_file_with',
]


def with_pil() -> BytesIO:
    """
    Takes a screenshot using the `PIL` library.

    This function is intended to be given as an argument to functions
    such as `screen_as_photo_with`, `screen_as_file_with`.
    """

    from PIL import ImageGrab

    screenshot = ImageGrab.grab()
    img = BytesIO()
    img.name = 'pil.png'  # Telegram doesn't like unnamed files
    screenshot.save(img, 'PNG')
    img.seek(0)
    return img

def with_grim() -> BytesIO:
    """
    Takes a screenshot using the `grim` tool.

    This function is intended to be given as an argument to functions
    such as `screen_as_photo_with`, `screen_as_file_with`.
    """

    import subprocess

    grim = subprocess.run(['grim', '-t', 'png', '/proc/self/fd/1'], stdout=subprocess.PIPE)
    img = BytesIO()
    img.name = 'grim.png'  # Telegram doesn't like unnamed files
    img.write(grim.stdout)
    img.seek(0)
    return img

def take_screenshot_with_or_complain_to(
    screenshot_method: Callable[[], IO[bytes]],
    bot: telebot.TeleBot,
    message: telebot.types.Message
) -> Optional[IO[bytes]]:
    try:
        screenshot = screenshot_method()
    except Exception as e:
        bot.reply_to(message, f"Error: your machine doesn't seem to support this:\n{e}")
    else:
        return screenshot

def screen_as_photo_with(
    screenshot_method: Callable[[], IO[bytes]]
) -> Callable[[telebot.TeleBot, telebot.types.Message, str], None]:
    """
    Given a screenshot method (e.g., `with_pil` or `with_grim`),
    returns an action function that takes a screenshot and sends it as a photo.
    """

    @help_description("Take a screenshot and send as a photo")
    def screen(bot: telebot.TeleBot, message: telebot.types.Message, _: str) -> None:
        img = take_screenshot_with_or_complain_to(screenshot_method, bot, message)
        if img:
            bot.send_photo(message.chat.id, img, reply_to_message_id=message.message_id)

    return screen

def screen_as_file_with(
    screenshot_method: Callable[[], IO[bytes]]
) -> Callable[[telebot.TeleBot, telebot.types.Message, str], None]:
    """
    Given a screenshot method (e.g., `with_pil` or `with_grim`),
    returns an action function that takes a screenshot and sends it as a file (document).
    """

    @help_description("Take a screenshot and send as a document")
    def screenf(bot: telebot.TeleBot, message: telebot.types.Message, _: str) -> None:
        img = take_screenshot_with_or_complain_to(screenshot_method, bot, message)
        if img:
            bot.send_document(message.chat.id, img, reply_to_message_id=message.message_id)

    return screenf
