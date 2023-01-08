#!/usr/bin/env python3

# Use this script to clear Telegram's cache of messages not yet processed by the bot.
# This can be useful after `!SHUTDOWN` if malefactor has sent messages with commands
# after you stopped the bot.

import telebot

from config import bot_token


bot = telebot.TeleBot(bot_token)


@bot.message_handler(func=lambda message: True)
def any_message(message):
    print(f"Received message from {message.chat.id} with text {message.text}\n")


if __name__ == "__main__":
    bot.polling(none_stop=True)
