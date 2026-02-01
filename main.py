#!/usr/bin/env python
# pylint: disable=unused-argument
import logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
import sqlite3 as sql
sql.threadsafety = 3 # https://docs.python.org/3/library/sqlite3.html#sqlite3.threadsafety
import asyncio
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from datetime import datetime

def birthday_logic(application: Application):
    import birthday
    bdays, callers = birthday.get_all_birthdays()
    current_year = datetime.now().year
    current_month = datetime.now().month
    current_day = datetime.now().day
    current_hour = datetime.now().hour
    for index, bday in enumerate(bdays):
        caller_id, bday_str, comment, last_notified_year = bday
        if current_year >= last_notified_year:
            continue
        parsed_date = datetime.strptime(bday_str, birthday.SQL_DATE_FORMAT).date()
        if parsed_date.month != current_month:
            continue
        if parsed_date.day != current_day:
            continue
        for caller in callers: # TODO: slow
            if caller[0] == caller_id:
                caller_hour = caller[1]
                break
        if caller_hour > current_hour:
            continue

        # Finally we should send a message here:
        Bot(application.bot).send_message(chat_id=caller_id, text=f"С днем рождения, {comment}!")

        # Also increment year in db:
        birthday.actualize_birthday_last_notification(caller_id, index)

async def birthdays(application: Application):
    import birthday
    birthday.init_db_if_needed()
    print("birthday_logic bootstrapped")
    while True:
        try:
            birthday_logic(application)
        except Exception as e:
            print(e)
            pass
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
    text = update.message.text
    if text in ["эх", "эхх", "эххх", "эхххх", "эх)", "эх!", "эх."]:
        await update.message.reply_text("Эххх!")

async def handle_bdays(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    import birthday
    usage = """
Команды:
 /bday add дд.мм.гг Имечко Фамилия
 /bday get
 /bday delete номер
 /bday help
""".lstrip()
    caller_id = update.effective_chat.id
    text = update.message.text
    split_text = text.split(maxsplit=3)[1:] # + remove /bday
    if len(split_text) == 0 or split_text[0] == "help":
        await update.message.reply_text(usage)
        return
    
    cmd = split_text[0]
    if cmd == "get":
        bdays = birthday.get_birthdays(caller_id)
        if bdays[1] is None:
            await update.message.reply_text("В данном чате или лс нет дней рождения")
        
        resp = f"Уведомления приходят в ~{bdays[1][0]}:00 МСК:\n"
        for index, bday in enumerate(bdays[0]):
            caller_id, bday_str, comment, last_notified_year = bday
            bday_str_converted = datetime.strptime(bday_str, birthday.SQL_DATE_FORMAT).strftime(birthday.DATE_FORMAT)
            resp += f" {index + 1}: {bday_str_converted}, {comment}\n"
        await update.message.reply_text(resp)
        return
    
    if cmd == "add":
        if len(split_text) != 3:
            await update.message.reply_text("Использование: /bday add дд.мм.гг Имечко Фамилия")
            return
        await update.message.reply_text(birthday.add_birthday(caller_id, split_text[1], split_text[2].replace("@", "")))
        return
    if cmd == "delete" or cmd == "remove":
        if len(split_text) != 2:
            await update.message.reply_text("Использование: /bday delete номер")
            return
        await update.message.reply_text(birthday.remove_birthday(caller_id, split_text[1], True))
        return

    await update.message.reply_text("а?")

def main() -> None:
    with open("SECRET.txt", "r") as secret_file:
        SECRET = secret_file.read().rstrip()
    application = Application.builder().token(SECRET).build()
    application.add_handler(CommandHandler("ai", echo))
    application.add_handler(CommandHandler("bday", handle_bdays))
    # COMMAND HANDLERS MUST BE BEFORE MESSAGE HANDLERS IN CODE.....
    application.add_handler(MessageHandler(filters.USER, echo_ehh))
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(birthdays(application))
    application.run_polling(allowed_updates=Update.MESSAGE)

if __name__ == "__main__":
    main()
