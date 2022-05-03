# リモコン (Rimokon)

Telegram bot for simple remote control of the device it is running on.

## Requirements / limitations

- To run the bot, on the device you need Python 3 and pip3 and have the libraries
  installed:
  ```
  pip3 install -r requirements.txt
  ```

- For the graphics-related controls (`/type`, `/key`) to work, you have to be running
  Xorg (typical for Linux) with the `xdotool` utility installed

- The tool is originally developed for Linux. Shell-related commands for Windows
  should be working just fine, but graphics-related controls are not supported on
  Windows. I am not planning to add support for it, but if you wish to, you are
  welcome! If you implement it, feel free to file a pull request.

- For the bot to function you, of course, need to have internet connection. It does
  not need to be super stable though, because the bot shall automatically reconnect
  in case of a network issue after a timeout.

## Configuration

You must create and fill in the file `config.py`. Use `config.py.example` as an
example. Refer to comments in it for more details. You will need to register a bot
and get a token [@BotFather](https://t.me/BotFather) and get your telegram user id
[@myidbot](https://t.me/myidbot).

## Usage

To start the bot, start `main.py`.

Supported commands (leading slash can be omitted, lower/upper case do not matter):
- `/start` - Start the bot

- `/help` - List available commands (you can find details there)

- `/key <KEYS>` (**Xorg only**) - Generate keypress event for a key or a shortcut.
  `<KEYS>` should be a valid `xdotool` keysequence (case matters). Refer to
  `xdotool`'s list of keycodes for details.

- `/type <STRING>` (**Xorg only**) - Type the given text on the keyboard through
  keyboard events.

- `/screen` (**Windows, macOS or Xorg**) - Take a screenshot and send it as a Telegram
  photo.

- `/screenf` (-||-) - Just like `/screen`, but sends the screenshot as a document.

- `/exec <COMMAND & ARGS SHELL-STYLE>` - run the command without shell but with
  shell-style arguments splitting (quoting and escaping is supported)

- `/rawexec <COMMAND & ARGS WHITESPACE-SEPARATED>` - run the command without shell
  and split it by whitespaces, ignoring quotes and backslashes

- `/shell <SHELL COMMAND>` - run the command in shell.

## Security

Because this bot allows arbitrary code execution on the device it is running on, of course,
you should only allow access to it (`admins_ids` in the config file) to trusted accounts.
Still, should you have any kind of runtime security threat, for example, if one of the admin
accounts gets compromised, it is possible to perform the emergency shutdown.

### Emergency shutdown

To shut the bot down, any user can send the command `!SHUTDOWN` (exactly like this, in
upper case with an exclamation mark and no other symbols/whitespaces/etc). Note that this
will prevent the bot from accepting new requests (the script will exit and it won't resume
until you restart it manually), but the child processes executed by previous requests won't
be killed.

Note that it is perfectly fine to stop the bot with a usual keyboard interrupt. The
`!SHUTDOWN` command is intended for a case of emergency.

**WARNING:** by default, **EVERY USER**, not just the admins, is allowed to `!SHUTDOWN` the bot,
in case you loose access to the admin(s) account(s). If you want to prevent such behavior, go
to the `main.py` and uncomment the line that contains "with this line commented out ANYONE
can shut the bot down". If you do so, the command will only remain available to the admins.

### After shutdown

Even if some commands were sent to the bot _after_ it was stopped, Telegram maintains (for a
limited time) the queue of messages not yet processed by the bot. So, if when starting the bot
next time, the malefactor remains in the admins list (e.g. if a real admin account was
compromised but then restored), the bot _might_ still receive the malicious commands, even if
the corresponding messages were deleted.

Besides, it is possible that the `!SHUTDOWN` command itself is not marked as processed
(because the bot tries to stop itself ASAP), so it might receive this command again when
runned next time (and, therefore, exit immediately).

Thus, it is recommended to run `after_shutdown.py` after you `!SHUTDOWN` the bot before
you restart it again. It will print all the queued messages (if any) and new incoming
messages, while it is running, clearing the queue on the Telegram side. After that just stop
this process and run `main.py` as usually.

## Contributing

You are very welcome to contribute! Do you have a question? Ask me! Have you found a bug
or identified a flaw? Tell me about it (e.g. file an issue)! Do you have a feture
request/idea? Let's discuss it (e.g. file in issue)! Want to implement something (e.g.
Windows graphical environment support)? Do so, and submit a pull request!
