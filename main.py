#!/usr/bin/python3
from functools import wraps
from typing import Union, List
import subprocess
from threading import Thread

import telebot

from util import escape, try_decode_otherwise_repr as try_decode
from config import bot_token, admins_ids


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
            bot.reply_to(message, f"The command has completed, but I failed to send the response:\n{e}")
        if not expect_quick:
            # Sending a new message and deleting the old one instead of editing because running a command may
            # take a long time and we want to notify user when it's over
            bot.delete_message(message.chat.id, sent_message.message_id)

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


@bot.message_handler(commands=['start'])
def start(message: telebot.types.Message):
    bot.reply_to(message,
                 "Hello! I am リモコン (pronounced \"rimokon\", japanese for \"remote control\") "
                 "and I let my admins control the device I am running on. Click /help to "
                 "learn more"
    )

@bot.message_handler(commands=['help'])
@admins_only_handler
def help(message: telebot.types.Message):
    bot.reply_to(message,
                 "Hello. I currently have the following commands:\n\n"
                 "/type STRING - (xdotool) Type STRING on keyboard. All the characters, including "
                    "whitespaces, are taken into account, skipping one character (space or newline) after the "
                    "command name. For example, to type `' 1'` you would run `/type  1`\n\n"
                 "/key KEY_NAME - (xdotool) Press the key KEY_NAME on keyboard (can be a shortcut, e.g. "
                 "`ctrl+w`)\n\n"
                 "/exec\_raw COMMAND ARGS - execute COMMAND with command-line whitespace-separated arguments "
                    "ARGS. The string is interpreted as raw (i.e. quotes and backslash-escaping are not "
                    "supported)\n\n"
                 "/shell STRING - execute STRING in a shell\n\n"
                 "/shutdown - Stop this bot. Currently running child processes won't be killed. "
                    "WARNING: for security reasons, by default, this command can be executed by ANY USER, "
                    "not just the admins. Uncomment a line in the source code to prevent this behavior",
                 parse_mode="Markdown"
    )

@bot.message_handler(commands=['type'])
@admins_only_handler
def type(message):
    text_to_type = message.text[6:]
    run_command_and_notify(message, ['xdotool', 'type', text_to_type], expect_quick=True)

@bot.message_handler(commands=['key'])
@admins_only_handler
def key(message):
    key_name = message.text[5:]
    run_command_and_notify(message, ['xdotool', 'key', key_name], expect_quick=True)

@bot.message_handler(commands=['exec_raw'])
@admins_only_handler
def exec_raw(message):
    command = message.text[10:]
    run_command_and_notify(message, command.split())

@bot.message_handler(commands=['shell'])
@admins_only_handler
def shell(message):
    command = message.text[7:]
    run_command_and_notify(message, command, shell=True)

@bot.message_handler(commands=['shutdown'])
#@admins_only_handler  # WARNING: with this line commented out ANYONE can shut the bot down
def shutdown(message):
    bot.stop_polling()


if __name__ == "__main__":
    bot.polling(non_stop=True)
