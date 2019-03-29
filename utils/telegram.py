import logging

import settings
from telegram.bot import Bot

from utils.singleton import SingletonDecorator

logger = logging.getLogger(__name__)

SingletonTelegramBot = SingletonDecorator(Bot)
MY_CHAT_ID = 772974581
b = SingletonTelegramBot(settings.TELEGRAM_TOKEN)


def send_message(chat_id, text):
    return b.send_message(chat_id, text)


def send_me(text):
    return b.send_message(MY_CHAT_ID, text)
