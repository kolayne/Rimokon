#!/usr/bin/env python3
from functools import wraps
from threading import Thread #, Timer
from time import sleep
from sys import stderr
from traceback import format_exc

import telebot
from requests.exceptions import RequestException

from .util import cmd_get_action_name, cmd_get_rest
from .import_config import bot_token, admins_ids, \
        emergency_shutdown_command, emergency_shutdown_is_public, \
        quick_access_cmds, \
        unified_actions, help_text


hello_text = ("Hello! I am リモコン (pronounced \"rimokon\", japanese for \"remote control\") "
              "and I let my admins control the device I am running on. The available actions are "
              "listed under /help")


bot = telebot.TeleBot(bot_token)


# Decorator that prevents the actions when executed by a non-admin user.
# MUST be specified UNDER the `@bot.*_handler` decorator (that is, applied BEFORE it)
def admins_only_handler(original_handler):
        @wraps(original_handler)
        def handler(message, *args, **kwargs):
            if message.chat.id in admins_ids:
                return original_handler(message, *args, **kwargs)
            else:
                bot.reply_to(message, "You are not my admin. Ignored")

        return handler


@bot.message_handler(func=lambda message: cmd_get_action_name(message.text) == 'start')
def start(message: telebot.types.Message):
    if message.chat.id in admins_ids:
        keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        # `quick_access_cmds` should be an array of arrays of strings, the latter arrays represent lines
        # of buttons
        for line in quick_access_cmds:
            keyboard.add(*line)
    else:
        keyboard = None

    bot.reply_to(message, hello_text, reply_markup=keyboard)

@bot.message_handler(func=lambda message: cmd_get_action_name(message.text) == 'help')
@admins_only_handler
def help_(message: telebot.types.Message):
    bot.reply_to(message, help_text)

def shutdown(_):
    print("Stopping due to emergency shutdown command received", flush=True)

    # Default behavior: stop polling immediately, but the shutdown command might remain in
    # the unprocessed messages on Telegram side, so unless you run after_shutdown.py,
    # the bot might receive this command again when you start it next time.
    bot.stop_polling()

    # Alternative behavior (don't forget to import `threading.Timer`):
    # stop the bot after a small timeout. This will make sure that the shutdown command is
    # processed and the bot won't receive it again, however, it is theoretically less safe:
    # there is a chance that a malicious command will arrive in the one tenth of a second
    # interval.
    #Timer(0.1, bot.stop_polling).start()

if not emergency_shutdown_is_public:
    shutdown = admins_only_handler(shutdown)
bot.register_message_handler(
        shutdown,
        func=lambda message: message.text and message.text.strip() == emergency_shutdown_command.strip()
)

@bot.message_handler(func=lambda message: True)  # TODO: accept other content types
@admins_only_handler
def run_command(message):
    wanted_action_name = cmd_get_action_name(message.text)
    if wanted_action_name == '':
        bot.reply_to(message, "Error: empty action name (space after slash?)")
        return
    command_rest = cmd_get_rest(message.text)
    action_func = unified_actions.get(wanted_action_name)
    if action_func is None:
        bot.reply_to(message, "Error: unknown action name")
    else:
        Thread(target=action_func, args=(bot, message, command_rest)).start()


def main():
    while True:
        try:
            bot.polling(non_stop=True)
            break  # If successfully stopped polling, should not retry
        except RequestException:
            # If internet connection issue, wait a little and restart
            print("Having internet connection issues. Retrying in 3 seconds...", file=stderr)
            print(format_exc(), file=stderr)
            sleep(3)
            print("Restarted\n", file=stderr)


if __name__ == "__main__":
    main()
