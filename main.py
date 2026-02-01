#!/usr/bin/env python
# pylint: disable=unused-argument

import logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

import sqlite3 as sql
sql.threadsafety = 3 # https://docs.python.org/3/library/sqlite3.html#sqlite3.threadsafety
import asyncio

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from datetime import datetime

logger = logging.getLogger(__name__)

last_returned_date = datetime.date()

async def birthdays():
    WANT_MINUTE = 59
    minute = datetime.now().minute
    while True:
        print("Every 1 hour")
        await asyncio.sleep(60 * 60)

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    replied_to = update.message.reply_to_message
    if replied_to is not None:
        #await replied_to.reply_photo("ai.jpg")
        await replied_to.reply_text("Это нейросеть?")
    await update.message.delete()

def is_caller_admin(update: Update) -> bool:
    # Source - https://stackoverflow.com/a/74736279
    # Posted by CallMeStag
    # Retrieved 2026-02-01, License - CC BY-SA 4.0

    chat_admins = update.effective_chat.get_administrators()
    return update.effective_user in (admin.user for admin in chat_admins)

async def echo_ehh(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print(update.message.chat_id, update.effective_user.id)
    text = update.message.text
    if text in ["эх", "эхх", "эххх", "эхххх", "эх)", "эх!", "эх."]:
        await update.message.reply_text("Эххх!")

def main() -> None:
    with open("SECRET.txt", "r") as secret_file:
        SECRET = secret_file.read().rstrip()
    application = Application.builder().token(SECRET).build()
    application.add_handler(CommandHandler("ai", echo))
    application.add_handler(MessageHandler(filters.USER, echo_ehh))
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(birthdays())
    application.run_polling(allowed_updates=Update.MESSAGE)
    #application.run_polling(allowed_updates=Update.MESSAGE)
    #loop.run_forever()

if __name__ == "__main__":
    main()
