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
        emergency_shutdown_command, emergency_shutdown_public, \
        quick_access_cmds, \
        unified_actions


bot = telebot.TeleBot(bot_token)


# Decorator that prevents the actions when executed by a non-admin user.
# Must be specified UNDER the `@bot.*_handler` decorator (must be applied before it)
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
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    # `quick_access_cmds` should be an array of arrays of strings, the latter arrays represent lines
    # of buttons
    for line in quick_access_cmds:
        keyboard.add(*line)

    bot.reply_to(message,
                 "Hello! I am リモコン (pronounced \"rimokon\", japanese for \"remote control\") "
                 "and I let my admins control the device I am running on. Click /help to "
                 "learn more",
                 reply_markup=keyboard
    )

@bot.message_handler(func=lambda message: cmd_get_action_name(message.text) == 'help')
@admins_only_handler
def help_(message: telebot.types.Message):
    bot.reply_to(message, 'The version you are running is in the work-in-progress state')
    '''
    bot.reply_to(message,
                 "Hello\\. I currently have the following commands:\n\n"
                 "*\\(\\*\\)* /type _STRING_ \\- Type _STRING_ on keyboard\n\n"
                 "*\\(\\*\\)* /key \\[_ARGS_\\] _KEYS_ \\[_KEYS_\\.\\.\\.\\] \\- Generate keypress event for "
                 "key \\(e\\.g\\. `space`\\), shortcut \\(e\\.g\\. `ctrl+w`\\), or a sequence of them "
                 "\\(separated with spaces, e\\.g\\. `ctrl+w space`\\)\\. Additional arguments are forwarded "
                 "to `xdotool key`\n\n"
                 "*\\(\\*\\*\\)* /screen \\- Capture screen and send the screenshot as a photo\n\n"
                 "*\\(\\*\\*\\)* /screenf \\- Capture screen and send the screenshot as a document\n\n"
                 "/run _COMMAND ARGS_ \\- execute _COMMAND_ with command\\-line whitespace\\-sparated "
                    "arguments _ARGS_\\. Arguments can be quoted and escaped with backslashes\n\n"
                 "/rawrun _COMMAND ARGS_ \\- similar to /run, but escaping and quoting are not supported, "
                    "the string is interpreted as raw\n\n"
                 "/shell _STRING_ \\- execute _STRING_ in a shell\n\n"
                 "The emergency shutdown command that you have set in the config file will terminate the "
                    "bot\\.\n\n"
                 "*\\(\\*\\)* These commands only work with `xdotool` \n\n"
                 "*\\(\\*\\*\\)* These commands are guaranteed to work on Windows, macOS or Linux with X11\n\n"
                 "Note: leading slashes can be omitted in all of the above commands, case does not matter\\. ",
                 parse_mode="MarkdownV2"
    )
    '''

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

if not emergency_shutdown_public:
    shutdown = admins_only_handler(shutdown)
bot.register_message_handler(shutdown,
                             func=lambda message: message.text.strip() == emergency_shutdown_command.strip())

@bot.message_handler(func=lambda message: True)  # TODO: accept other content types
@admins_only_handler
def run_command(message):
    wanted_action_name = cmd_get_action_name(message.text)
    command_rest = cmd_get_rest(message.text)
    for action_name, action_func in unified_actions.items():
        if wanted_action_name == action_name:
            Thread(target=action_func, args=(bot, message, command_rest)).start()
            return
    bot.reply_to(message, "Unknown command")


if __name__ == "__main__":
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
