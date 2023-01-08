#!/usr/bin/env python3
from functools import wraps
from typing import Union, List
import subprocess
from threading import Thread #, Timer
import shlex
from time import sleep
from sys import stderr
from traceback import format_exc
from PIL import ImageGrab
from io import BytesIO

import telebot
from requests.exceptions import RequestException

from util import escape, try_decode_otherwise_repr as try_decode, cmd_get_action, cmd_get_rest
from config import bot_token, admins_ids
try:
    from config import quick_access_cmds
except ImportError:
    quick_access_cmds = []


bot = telebot.TeleBot(bot_token)


def run_command_and_notify(message: telebot.types.Message, args: Union[str, List[str]], *,
                           expect_quick: bool = False, shell: bool = False):
    """
    Creates and starts a new thread, that runs the given command (either in the shell mode or not) and
    reports the results to the user.

    @param message: Telegram bot message to reply to
    @param args: String or list of arguments to be executed.
    @param expect_quick: (optional, default `False`) Whether to expect that the command will
        finish quickly. If so, bot will only notify the user after it completes, otherwise it
        will send a temporary message to identify that the command is accepted and running,
        but not yet finished.
    @param shell: (optional, default `False`) Whether to run in shell
    """
    def f():
        try:
            p = subprocess.Popen(args, shell=shell, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)

            if not expect_quick:
                sent_message = bot.reply_to(message, "Executing...")

            out, err = map(try_decode, p.communicate())
            reply_text = "Done\\. Output:\n"  # '.' must be escaped in MarkdownV2
            if out:
                reply_text += "stdout:\n```\n" + escape(out, ['\\', '`']) + "\n```\n"
            if err:
                reply_text += "stderr:\n```\n" + escape(err, ['\\', '`']) + "\n```\n"
            reply_text += f"Exit code: {p.returncode}"

            try:
                bot.reply_to(message, reply_text, parse_mode="MarkdownV2")
            except telebot.apihelper.ApiTelegramException as e:
                bot.reply_to(message, f"The command has completed with code {p.returncode}, but I failed "
                                      f"to send the response:\n{e}")
            if not expect_quick:
                # Sending a new message and deleting the old one instead of editing because running a command may
                # take a long time and we want to notify user when it's over
                bot.delete_message(message.chat.id, sent_message.message_id)
        except Exception as e:
            bot.reply_to(message, f"Something went wrong while processing your request:\n{e}")

    Thread(target=f, daemon=True).start()  # Do all of it in the background


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


@bot.message_handler(func=lambda message: cmd_get_action(message.text) == 'start')
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

@bot.message_handler(func=lambda message: cmd_get_action(message.text) == 'help')
@admins_only_handler
def help_(message: telebot.types.Message):
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
                 "`!SHUTDOWN` \\- Stop this bot\\. Already running child processes won't be killed\\. "
                    "WARNING: for security reasons, by default, this command can be executed by ANY USER, "
                    "not just the admins\\. Uncomment a line in the source code to prevent this behavior\n\n"
                 "*\\(\\*\\)* These commands only work with `xdotool` \n\n"
                 "*\\(\\*\\*\\)* These commands are guaranteed to work on Windows, macOS or Linux with X11\n\n"
                 "Note: leading slashes can be omitted in all of the above commands, case does not matter\\. "
                 "The `!SHUTDOWN` command is an exception: it must be typed exactly like that",
                 parse_mode="MarkdownV2"
    )

@bot.message_handler(func=lambda message: cmd_get_action(message.text) == 'type')
@admins_only_handler
def type_(message):
    text_to_type = cmd_get_rest(message.text)
    run_command_and_notify(message, ['xdotool', 'type', text_to_type], expect_quick=True)

@bot.message_handler(func=lambda message: cmd_get_action(message.text) == 'key')
@admins_only_handler
def key(message):
    xdotool_key_args = cmd_get_rest(message.text).split()
    run_command_and_notify(message, ['xdotool', 'key'] + xdotool_key_args, expect_quick=True)

@bot.message_handler(func=lambda message: cmd_get_action(message.text) in ['screen', 'screenf'])
@admins_only_handler
def screen(message):
    try:
        screenshot = ImageGrab.grab()
    except OSError as e:
        bot.reply_to(message, f"Error: your machine does not support this feature:\n{e}")
        return
    img = BytesIO()
    img.name = 'i.png'
    screenshot.save(img, 'PNG')
    img.seek(0)
    if cmd_get_action(message.text).endswith('f'):
        bot.send_document(message.chat.id, img, reply_to_message_id=message.message_id)
    else:
        bot.send_photo(message.chat.id, img, reply_to_message_id=message.message_id)

@bot.message_handler(func=lambda message: cmd_get_action(message.text) in ['run', 'rawrun', 'exec', 'rawexec'])
@admins_only_handler
def run_raw_run(message):
    action = cmd_get_action(message.text).replace('exec', 'run')
    to_run = cmd_get_rest(message.text)
    if action == 'run':
        try:
            to_run = shlex.split(to_run)
        except ValueError as e:
            bot.reply_to(message, f"Failed to parse arguments:\n{e}")
            return
    elif action == 'rawrun':
        to_run = to_run.split()
    else:
        assert False, "Neither /run, nor /rawrun. How is that possible?"
    run_command_and_notify(message, to_run)

@bot.message_handler(func=lambda message: cmd_get_action(message.text) == 'shell')
@admins_only_handler
def shell(message):
    to_run = cmd_get_rest(message.text)
    run_command_and_notify(message, to_run, shell=True)

@bot.message_handler(func=lambda message: message.text == '!SHUTDOWN')
#@admins_only_handler  # WARNING: with this line commented out ANYONE can shut the bot down
def shutdown(message):
    print("Stopping due to '!SHUTDOWN' received", flush=True)

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

@bot.message_handler(func=lambda message: True)
def unknown(message):
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
