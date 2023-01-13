from functools import wraps
from typing import Callable, Any

from telebot import TeleBot
from telebot.types import Message


def _run_notified(f, bot, message, args, kwargs):
    sent_message = bot.reply_to(message, "Executing...")
    try:
        return f(bot, message, *args, **kwargs)
    finally:
        bot.delete_message(message.chat.id, sent_message.message_id)

def notify_of_execution(f: Callable[[TeleBot, Message, ...], Any]) -> Callable[[TeleBot, Message, ...], Any]:
    """
    Decorator for an action function to notify user when the execution of the action is in progress.

    Modifies an action function (which accepts `telebot.TeleBot` and `telebot.Message` as its first
    positional arguments) to send a message with text "Executing..." before starting the action function
    and deletes that message after its completion.
    """
    @wraps(f)
    def decorated(bot: TeleBot, message: Message, *args, **kwargs):
        return _run_notified(f, bot, message, args, kwargs)
    return decorated

def notify_of_execution_conditionally(f: Callable[[TeleBot, Message, ...], Any]) -> \
        Callable[[TeleBot, Message, ...], Any]:
    """
    Decorator for an action function to conditionally notify user when the execution of the
    action is in progress.

    Modifes an action function (which accepts `telebot.TeleBot` and `telebot.Message` as its
    first position arguments) such that an additional kw-only argument `notify` is added to
    the function. If it is `True` (default), the behavior is the same with `notify_of_execution`;
    if it is `False`, the behavior is as if the function was unmodified
    """
    @wraps(f)
    def decorated(bot: TeleBot, message: Message, *args, notify: bool = True, **kwargs):
        if notify:
            return _run_notified(f, bot, message, args, kwargs)
        else:
            return f(bot, message, *args, **kwargs)
    return decorated
