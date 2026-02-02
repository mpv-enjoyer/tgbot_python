import sqlite3 as sql
sql.threadsafety = 3 # https://docs.python.org/3/library/sqlite3.html#sqlite3.threadsafety
import os
from datetime import datetime
from zoneinfo import ZoneInfo
import asyncio

TABLE_CALLERS = "callers"
TABLE_BIRTHDAYS = "birthdays"
LIMIT_BIRTHDAYS_PER_CALLER = 50
DATE_FORMAT = "%d.%m.%Y"
SQL_DATE_FORMAT = "%Y-%m-%d"
BIRTHDAYS_DB_FILE_PATH = "birthdays.db"

cur: sql.Cursor
con: sql.Connection
lock = asyncio.Lock()

# Returns (list(caller_id, birthday, comment, int(last_notified_year)), int(update_on_hour))
async def get_birthdays(caller_id: int, acquire_lock = True):
    global lock
    def logic():
        global cur
        res = cur.execute(f"SELECT * FROM {TABLE_BIRTHDAYS} WHERE caller_id=? ORDER BY birthday", (caller_id,)).fetchall()
        res2 = cur.execute(f"SELECT update_on_hour FROM {TABLE_CALLERS} WHERE caller_id=?", (caller_id,)).fetchone()
        return res, res2
    
    if acquire_lock:
        async with lock:
            return logic()
    else:
        return logic()

# Returns (list(caller_id, birthday, comment, int(last_notified_year)), list(caller_id, int(update_on_hour)))
async def get_all_birthdays(acquire_lock = True):
    global lock
    def logic():
        global cur
        res = cur.execute(f"SELECT * FROM {TABLE_BIRTHDAYS} ORDER BY birthday").fetchall()
        res2 = cur.execute(f"SELECT * FROM {TABLE_CALLERS}").fetchall()
        return res, res2
    
    if acquire_lock:
        async with lock:
            return logic()
    else:
        return logic()

async def add_birthday(caller_id: str, date: str, comment: str) -> str:
    global lock
    async with lock:
        global cur, con
        try:
            parsed_date_before_1k_year_check = datetime.strptime(date, DATE_FORMAT)
            if parsed_date_before_1k_year_check.year < 1000:
                # Python bug here:
                #  >>> dt.strptime("01.02.0003", "%d.%m.%Y").strftime("%d.%m.%Y")
                #  '01.02.3'
                #  >>> dt.strptime("01.02.3", "%d.%m.%Y")
                #  ValueError: time data '01.02.3' does not match format '%d.%m.%Y'
                return "Нельзя ввести год меньше 1000"
            sql_date = parsed_date_before_1k_year_check.strftime(SQL_DATE_FORMAT)
            caller_id = int(caller_id)
        except Exception as e:
            return f"Вводите дату в формате дд.мм.гггг: {e}"

        if cur.execute(f"SELECT * FROM {TABLE_CALLERS} WHERE caller_id={caller_id}").fetchone() is None:
            DEFAULT_NOTIFICATION_TIME = 12
            cur.execute(f"INSERT INTO {TABLE_CALLERS} VALUES (?, ?)", (caller_id, DEFAULT_NOTIFICATION_TIME))
        elif len((await get_birthdays(caller_id, acquire_lock=False))[0]) >= LIMIT_BIRTHDAYS_PER_CALLER:
            return f"Слишком много дней рождения для одного человека/чата: {LIMIT_BIRTHDAYS_PER_CALLER}"

        cur.execute(f"INSERT INTO {TABLE_BIRTHDAYS} VALUES (?, ?, ?, ?)", (caller_id, sql_date, comment, datetime.now(ZoneInfo('Europe/Moscow')).year - 1))
        con.commit()
        return f"Добавлен день рождения для {comment} на дату {date}"

async def actualize_birthday_last_notification(global_offset: str):
    global lock
    async with lock:
        global cur, con
        what = f"UPDATE {TABLE_BIRTHDAYS} SET last_notified_year = {datetime.now(ZoneInfo('Europe/Moscow')).year} WHERE rowid = (SELECT rowid FROM {TABLE_BIRTHDAYS} ORDER BY birthday LIMIT 1 OFFSET {global_offset});"
        cur.execute(what)
        con.commit()
        print("actualize_birthday_last_notification successful!")

async def remove_birthday(caller_id: str, offset: str, convert_from_user_friendly = False):
    global lock
    async with lock:
        global cur, con
        try:
            offset = int(offset)
            if convert_from_user_friendly:
                offset -= 1
            caller_id = int(caller_id)
        except Exception as e:
            return f"Неверные данные для удаления: {e}"

        if offset < 0:
            return f"Неверный номер для удаления"

        row = cur.execute(f"SELECT * FROM {TABLE_BIRTHDAYS} WHERE rowid = (SELECT rowid FROM {TABLE_BIRTHDAYS} WHERE caller_id = {caller_id} ORDER BY birthday LIMIT 1 OFFSET {offset});").fetchone()
        if row is None:
            return f"Неверный номер для удаления: {offset}"

        len_before = len((await get_birthdays(caller_id, acquire_lock=False))[0])
        what = f"DELETE FROM birthdays WHERE rowid = (SELECT rowid FROM birthdays WHERE caller_id = {caller_id} ORDER BY birthday LIMIT 1 OFFSET {offset});"

        cur.execute(what)
        con.commit()
        len_after = len((await get_birthdays(caller_id, acquire_lock=False))[0])
        if len_before == len_after:
            return "ERR: unexpected len_before != len_after"
        return f"Удален день рождения {row[2]}"

async def init_db_if_needed():
    global lock
    async with lock:
        global cur, con
        con = sql.connect(BIRTHDAYS_DB_FILE_PATH)
        cur = con.cursor()
        # https://sqlite.org/datatype3.html#date_and_time_datatype
        cur.execute(f"CREATE TABLE IF NOT EXISTS {TABLE_CALLERS}(caller_id INTEGER PRIMARY KEY, update_on_hour INTEGER)")
        cur.execute(f"CREATE TABLE IF NOT EXISTS {TABLE_BIRTHDAYS}(caller_id INTEGER, birthday DATE, comment TINYTEXT, last_notified_year INTEGER, FOREIGN KEY (caller_id) REFERENCES caller(caller_id))")
        con.commit()

def main():
    DEBUG_CALLER = "576527597"
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(init_db_if_needed())

    user_input = ""
    while user_input != "exit":
        user_input = input()
        user_input_split = user_input.split(maxsplit=2)
        if len(user_input_split) == 0:
            continue
        cmd = user_input_split[0]
        if cmd == "get":
            print(loop.run_until_complete(get_all_birthdays()))
        if cmd == "add" and len(user_input_split) == 3:
            print(loop.run_until_complete(add_birthday(DEBUG_CALLER, user_input_split[1], user_input_split[2])))
        if cmd == "del" and len(user_input_split) == 2:
            print(loop.run_until_complete(remove_birthday(DEBUG_CALLER, user_input_split[1])))
        if cmd == "act":
            # Dangerous thus disabled! Disables every birthday in DB until the next year.
            count = len(loop.run_until_complete(get_birthdays(DEBUG_CALLER)[0]))
            for i in range(count):
                pass
                #actualize_birthday_last_notification(DEBUG_CALLER, i)
        if user_input == "exit":
            break

if __name__ == "__main__":
    main()