#!/usr/bin/env python
# pylint: disable=unused-argument
# This program is dedicated to the public domain under the CC0 license.
import logging
import sqlite3

from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user                                                             
    await update.message.reply_html("started", )

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    replied_to = update.message.reply_to_message
    if replied_to is not None:
        #await replied_to.reply_photo("ai.jpg")
        await replied_to.reply_text("Это нейросеть?")
    await update.message.delete()

async def echo_ehh(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    if text in ["эх", "эхх", "эххх", "эхххх", "эх)", "эх!", "эх."]:
        await update.message.reply_text("Эххх!")

def main() -> None:
    with open("SECRET.txt", "r") as secret_file:
        SECRET = secret_file.read().rstrip()
    application = Application.builder().token(SECRET).build()
    application.add_handler(CommandHandler("ai", echo))
    application.add_handler(MessageHandler(filters.USER, echo_ehh))
    application.run_polling(allowed_updates=Update.MESSAGE)

if __name__ == "__main__":
    main()
