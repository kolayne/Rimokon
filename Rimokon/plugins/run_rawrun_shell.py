from typing import Union, List
from subprocess import Popen, PIPE
from shlex import split as shlex_split

from telebot import TeleBot
from telebot.types import Message
from telebot.apihelper import ApiTelegramException

from .plugin_helpers import notify_of_execution_conditionally


__all__ = ['shell', 'run', 'rawrun', 'run_parsed_command']


def try_decode_otherwise_repr(s: bytes) -> str:
    try:
        return s.decode()
    except UnicodeDecodeError:
        return repr(s)


def _escape(where: str, what: List[str]):
    # If there is a backslash in `what`, it must come first
    if '\\' in what[1:]:
        what = ['\\'] + [c for c in what if c != '\\']

    for c in what:
        assert len(c) == 1
        where = where.replace(c, '\\' + c)
    return where


@notify_of_execution_conditionally
def run_parsed_command(bot: TeleBot, message: Message, command: Union[str, List[str]],
                       *, shell: bool = False) -> None:
    """
    Accepts a command (in the prepared form), runs it via `subprocess.Popen`, forms and sends
    the response message.
    """
    p = Popen(command, shell=shell, stdin=PIPE, stdout=PIPE, stderr=PIPE)

    out, err = map(try_decode_otherwise_repr, p.communicate())
    reply_text = "Done\\. Output:\n"  # '.' must be escaped in MarkdownV2
    if out:
        reply_text += "stdout:\n```\n" + _escape(out, ['\\', '`']) + "\n```\n"
    if err:
        reply_text += "stderr:\n```\n" + _escape(err, ['\\', '`']) + "\n```\n"
    reply_text += f"Exit code: {p.returncode}"

    try:
        bot.reply_to(message, reply_text, parse_mode="MarkdownV2")
    except ApiTelegramException as e:
        bot.reply_to(message, f"The command has completed with code {p.returncode}, but I failed "
                              f"to send the response:\n{e}")

def shell(bot: TeleBot, message: Message, command_rest: str, *, notify: bool = True) -> None:
    run_parsed_command(bot, message, command_rest, shell=True, notify=notify)

def run(bot: TeleBot, message: Message, command_rest: str, *, notify: bool = True) -> None:
    try:
        command = shlex_split(command_rest)
    except ValueError as e:
        bot.reply_to(message, f"Failed to parse arguments:\n{e}")
    else:
        run_parsed_command(bot, message, command, notify=notify)

def rawrun(bot: TeleBot, message: Message, command_rest: str, *, notify: bool = True) -> None:
    run_parsed_command(bot, message, command_rest.split(), notify=notify)
