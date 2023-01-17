from functools import wraps
from typing import Callable, Any

from telebot import TeleBot
from telebot.types import Message


def with_help_description(f: Callable, help_message: str) -> Callable:
    """
    Sets the message `help_message` to be displayed for the action function `f` in the bot's /help.
    Modifies the input function and returns it.

    Example:

    def echo_action_function(bot: telebot.TeleBot, msg: telebot.types.Message, rest: str):
        bot.reply_to(msg, rest)
    with_help_description(echo_action_function, "Replies with the rest of the message after the action name")
    """
    setattr(f, 'RimokonHelp', help_message)
    return f

def help_description(help_message: str):
    """
    Add message corresponding to this action to display in the bot's /help.
    Modifies the input function and returns it.

    Example:

    @help_description("Replies with the rest of the message after the action name")
    def echo_action_function(bot: telebot.TeleBot, msg: telebot.types.Message, rest: str):
        bot.reply_to(msg, rest)

    """
    def decorate(f: Callable) -> Callable:
        return with_help_description(f, help_message)
    return decorate


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
