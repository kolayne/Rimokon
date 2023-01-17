"""
This file imports the user-defined config.py file and processes all the entries to
bring them to the common form and make it easy to use them.
"""

import logging
from functools import wraps

from .util import cmd_get_action_name, cmd_get_rest
from .config import bot_token, admins_ids, \
        quick_access_cmds, \
        emergency_shutdown_command, emergency_shutdown_public, \
        actions, aliases


logger = logging.getLogger('Rimokon')
_handler = logging.StreamHandler()
_handler.setFormatter(logging.Formatter(
    fmt='%(asctime)s %(levelname)s\t%(message)s', datefmt="%d.%m.%Y %H:%M:%S"))
logger.addHandler(_handler)
del _handler  # Make unimportable


def die(*args):
    # TODO: use logger object
    logger.critical(*args)
    exit(1)

def canonicalize_key_or_die(k_: str) -> str:
    """
    Bring the key to the lowercase stripped and slash-stripped form.

    If the given name is not a valid action name print the error message and terminate the program.
    """
    k = k_.strip().lstrip('/').lower()
    if any(c.isspace() for c in k):
        die('Action name must not contain whitespaces (violated by %s)', repr(k_))
    return k


def make_action_noexcept(action_func):
    @wraps(action_func)
    def noexcept_action_func(bot, message, *args, **kwargs):
        try:
            return action_func(bot, message, *args, **kwargs)
        except Exception as e:
            # Logger functions must never ever raise exceptions, right? It should be safe to use them
            # outside of the try block.
            logger.exception('Exception occurred while handling the command %s', message.text)
            try:
                bot.reply_to(message, f"Something went wrong while processing your request:\n{e}")
            except Exception:
                logger.exception('Failed to notify user of the above problem')
            else:
                logger.info('Successfully notified user of the above problem')
    return noexcept_action_func


updated_actions = {}

for k_, v in actions.items():
    logger.debug('Processing action %s', repr(k_))
    k = canonicalize_key_or_die(k_)
    if k in updated_actions.keys():
        die('Attempt to redefine action %s (in `config.actions`)', repr(k))
    if not callable(v):
        die('The action function specified by key %s is not callable', repr(k_))
    updated_actions[k] = make_action_noexcept(v)


def complex_alias_from_string(base_action_func, prepended_string):
    """
    Construct the action function for a string alias, given its base action function and the
    prepended string for the command.
    """
    def new_action_func(bot, msg, _rest):
        # Using `cmd_get_rest(msg.text, ...)` instead of `_rest` to preserve the whitespace
        # symbol from the message text.
        new_rest = prepended_string + cmd_get_rest(msg.text, False)

        logger.debug('String alias triggered. Message text: %s; prepended string: %s; '
                      'resulting (new) rest: %s',
                      repr(msg.text), repr(prepended_string), repr(new_rest))

        return base_action_func(bot, msg, new_rest)

    return new_action_func


updated_aliases = {}

for k_, v_ in aliases.items():
    logger.debug('Processing alias %s', repr(k_))
    k = canonicalize_key_or_die(k_)
    if k in updated_aliases.keys():
        die('Attempt to redefine alias %s (in `config.aliases`)', repr(k))
    if k in updated_actions.keys():
        die('Alias %s attempts to overwrite an existing action', repr(k_))
    if isinstance(v_, str):
        base_plugin = cmd_get_action_name(v_)
        if base_plugin not in updated_actions.keys():
            die('Alias %s relies on the action %s which does not exist. '
                'Note that aliases for aliases are not supported', repr(k_), repr(base_plugin))
        base_action_func = updated_actions[base_plugin]

        v = complex_alias_from_string(base_action_func, cmd_get_rest(v_))
    elif callable(v_):
        v = v_
    else:
        die('The alias %s specifies neither a string nor a callable object', repr(k_))
    updated_aliases[k] = make_action_noexcept(v)


unified_actions = {**updated_actions, **updated_aliases}

# Make the old intermediate values unimportable
del actions, aliases, updated_actions, updated_aliases


# When executed as a script, behave as a config checker. Otherwise just notify of success
(print if __name__ == "__main__" else logger.info)("Successfully imported the config file")
