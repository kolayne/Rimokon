# リモコン (Rimokon)

Telegram bot for simple remote control of the device it is running on.

## Redesign in progress

The current readme is mainly outdated.

<s>

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
- `/start` - Start the bot, update keyboard on Telegram side

- `/help` - List available commands (you can find details there)

- `/key [&lt;ARGS&gt;] &lt;KEYS&gt; [&lt;KEYS&gt;...]` (**Xorg only**) - Generate keypress event for a key,
  a shortcut, or a sequence of them. All the arguments are separated by space and forwarded
  to `xdotool key`, thus, `&lt;KEYS&gt;` must be valid `xdotool` keysequences, and it is possible
  to specify additional arguments `&lt;ARGS&gt;` (refer to `xdotool key --help` for details)

- `/type &lt;STRING&gt;` (**Xorg only**) - Type the given text on the keyboard through
  keyboard events.

- `/screen` (**Windows, macOS or Xorg**) - Take a screenshot and send it as a Telegram
  photo.

- `/screenf` (-||-) - Just like `/screen`, but sends the screenshot as a document.

- `/run &lt;COMMAND &amp; ARGS SHELL-STYLE&gt;` - run the command without shell but with
  shell-style arguments splitting (quoting and escaping is supported)

- `/rawrun &lt;COMMAND &amp; ARGS WHITESPACE-SEPARATED&gt;` - run the command without shell
  and split it by whitespaces, ignoring quotes and backslashes

- `/shell &lt;SHELL COMMAND&gt;` - run the command in shell.

Note: `/exec` and `/rawexec` are synonyms for `/run` and `/rawrun` respectively (for
backward compatibility).

</s>

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
