from typing import Union, List
from subprocess import Popen, PIPE
from shlex import split as shlex_split

from telebot import TeleBot
from telebot.types import Message
from telebot.apihelper import ApiException

from .plugin_helpers import notify_of_execution_conditionally, help_description


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

    if p.returncode >= 0:
        reply_text += f"Exit code: {p.returncode}"
    else:  # Negative `.returncode` denotes the POSIX signal which killed the process
        reply_text += f"Exited due to signal {-p.returncode}"

    try:
        bot.reply_to(message, reply_text, parse_mode="MarkdownV2")
    except ApiException as e:
        bot.reply_to(message, f"The command has completed with code {p.returncode}, but I failed "
                              f"to send the response:\n{e}")

@help_description("<COMMAND> Run command in default shell")
def shell(bot: TeleBot, message: Message, command_rest: str, *, notify: bool = True) -> None:
    # pylint: disable=unexpected-keyword-arg
    run_parsed_command(bot, message, command_rest, shell=True, notify=notify)

@help_description("<COMMAND> Run command outside of shell (quoting and escaping is supported)")
def run(bot: TeleBot, message: Message, command_rest: str, *, notify: bool = True) -> None:
    try:
        command = shlex_split(command_rest)
    except ValueError as e:
        bot.reply_to(message, f"Failed to parse arguments:\n{e}")
    else:
        # pylint: disable=unexpected-keyword-arg
        run_parsed_command(bot, message, command, notify=notify)

@help_description("<COMMAND> Run command outside of shell (split by space, no quoting or escaping)")
def rawrun(bot: TeleBot, message: Message, command_rest: str, *, notify: bool = True) -> None:
    # pylint: disable=unexpected-keyword-arg
    run_parsed_command(bot, message, command_rest.split(), notify=notify)
