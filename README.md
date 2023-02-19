# リモコン (Rimokon)

Telegram bot for simple remote control of the device it is running on.

## Redesign in progress

The current readme is mainly outdated.


## Basic usage

-  Install requirements:
   ```
   pip3 install -r requirements.txt
   ```


-  Copy `Rimokon/config.py.example` to `Rimokon/config.py` and modify it according to your use case.
   Optionally, install `xdotool`/`ydotool` or a similar utility for keyboard manipulations.
   Use [@BotFather](https://t.me/BotFather) to acquire a Telegram bot token.


-  Run the bot as a python package: `python3 -m Rimokon` or, from another directory,
   `python3 -m Path.To.Rimokon.With.Dot.Delimiters`


## Plugins, actions, and aliases

Plugins are python packages stored under `Rimokon/plugins/`, which export some functions of the
signature `f(bot: telebot.TeleBot, message: telebot.types.Message, rest: str) -> Any`. It will
be called with three positional arguments: bot object to perform actions, the message that
triggered the action, and the string containing the part of the command after the action name.

To enable a package, put it to the `Rimokon/plugins/` directory, import it in your
`Rimokon/config.py` and include it to the `actions` dictionary.

Aliases are, roughly speaking, user-defined actions. They may take the form of a string
(e.g. `'key': 'run xdotool key'` causes commands like `key space` be interpreted like
`run xdotool key space`) or an action-like function, in which case they behave just like
the usual actions (e.g. `'echo': lambda bot, msg, rest: bot.reply_to(msg, rest)` will make
the command `echo 123 456 789` produce the response `123 456 789`).

To enable an alias, define it in your `Rimokon/config.py` in the `aliases` dictionary.


## Adavnced usage, technical plugins details, ...

More detailed docs are coming (hopefully, soon) in the GitHub wikis... But not yet 😔.
Meanwhile, feel free to spam in the issues.


## Security

Because this bot allows arbitrary code execution on the device it is running on, of course,
you should only allow access to it (`admins_ids` in the config file) to trusted accounts.
Still, should you have any kind of runtime security threat, for example, if one of the admin
accounts gets compromised, it is possible to perform the emergency shutdown.


### Emergency shutdown

To shut the bot down, user must send the command that they define in the config.py file.
Unlike other commands, this command must exactly match the configured string
(e.g. lowercase/capital letters mismatch are not allowed), except for the leading and trailing
whitespaces (they are ignored). This will prevent the bot from accepting new requests
(the bot will exit and it won't resume until you restart it manually), but the child processes
started by previous requests won't be killed.

It is also possible (and recommended) to configure the bot to accept the emergency shutdown
command from all users, not just the admins. This is useful in case an admin looses access
to their account to a malicious user.

Note that it is perfectly fine to stop the bot with a usual keyboard interrupt. The shutdown
command is intended for a case of emergency.


### After emergency shutdown

Even if some commands were sent to the bot _after_ it was stopped, Telegram maintains (for a
limited time) the queue of messages not yet processed by the bot. So, if when starting the bot
next time, the malefactor remains in the admins list (e.g. if a real admin account was
compromised but then restored), the bot _might_ still receive the malicious commands, even if
the corresponding messages were deleted.

Besides, it is possible that the emergency shutdown command itself is not marked as processed
(because the bot tries to stop itself ASAP), so it might receive this command again when
runned next time (and, therefore, exit immediately).

Thus, it is recommended to run `after_shutdown.py` after emergency shutdown of the bot before
it is restarted. It will print all the queued messages (if any) and new incoming
messages, while it is running, clearing the queue on the Telegram side. After that just stop
this process and run `main.py` as usually.

## Contributing

You are very welcome to contribute! Do you have a question? Ask me! Have you found a bug
or identified a flaw? Tell me about it (e.g. file an issue)! Do you have a feture
request/idea? Let's discuss it (e.g. file in issue)! Want to implement something (e.g.
Windows graphical environment support)? Do so, and submit a pull request!
