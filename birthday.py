import sqlite3 as sql
sql.threadsafety = 3 # https://docs.python.org/3/library/sqlite3.html#sqlite3.threadsafety
import os
import datetime

TABLE_CALLERS = "callers"
TABLE_BIRTHDAYS = "birthdays"
LIMIT_BIRTHDAYS_PER_CALLER = 50
DATE_FORMAT = "%d.%m.%Y"
SQL_DATE_FORMAT = "%Y-%m-%d"
BIRTHDAYS_DB_FILE_PATH = "birthdays.db"

cur: sql.Cursor
con: sql.Connection

# Returns (list(caller_id, birthday, comment, int(last_notified_year)), int(update_on_hour))
def get_birthdays(caller_id: int):
    global cur
    res = cur.execute(f"SELECT * FROM {TABLE_BIRTHDAYS} WHERE caller_id=? ORDER BY birthday", (caller_id,)).fetchall()
    res2 = cur.execute(f"SELECT update_on_hour FROM {TABLE_CALLERS} WHERE caller_id=?", (caller_id,)).fetchone()
    return res, res2

# Returns (list(caller_id, birthday, comment, int(last_notified_year)), list(caller_id, int(update_on_hour)))
def get_all_birthdays():
    global cur
    res = cur.execute(f"SELECT * FROM {TABLE_BIRTHDAYS} ORDER BY birthday").fetchall()
    res2 = cur.execute(f"SELECT * FROM {TABLE_CALLERS}").fetchall()
    return res, res2

def add_birthday(caller_id: str, date: str, comment: str) -> str:
    global cur, con
    try:
        sql_date = datetime.datetime.strptime(date, DATE_FORMAT).strftime(SQL_DATE_FORMAT)
        caller_id = int(caller_id)
    except Exception as e:
        return f"Вводите дату в формате дд.мм.гг: {e}"

    if cur.execute(f"SELECT * FROM {TABLE_CALLERS} WHERE caller_id={caller_id}").fetchone() is None:
        DEFAULT_NOTIFICATION_TIME = 12
        cur.execute(f"INSERT INTO {TABLE_CALLERS} VALUES (?, ?)", (caller_id, DEFAULT_NOTIFICATION_TIME))
    elif len(get_birthdays(caller_id)[0]) >= LIMIT_BIRTHDAYS_PER_CALLER:
        return f"Слишком много дней рождения для одного человека/чата: {LIMIT_BIRTHDAYS_PER_CALLER}"

    cur.execute(f"INSERT INTO {TABLE_BIRTHDAYS} VALUES (?, ?, ?, ?)", (caller_id, sql_date, comment, datetime.datetime.now().year - 1))
    con.commit()
    return f"Добавлен день рождения для {comment} на дату {date}"

def actualize_birthday_last_notification(global_offset: str):
    global cur, con
    what = f"UPDATE {TABLE_BIRTHDAYS} SET last_notified_year = {datetime.datetime.now().year} WHERE rowid = (SELECT rowid FROM {TABLE_BIRTHDAYS} ORDER BY birthday LIMIT 1 OFFSET {global_offset});"
    cur.execute(what)
    con.commit()
    print("actualize_birthday_last_notification successful!")

def remove_birthday(caller_id: str, offset: str, convert_from_user_friendly = False):
    global cur, con
    try:
        offset = int(offset)
        if convert_from_user_friendly:
            offset -= 1
        caller_id = int(caller_id)
    except Exception as e:
        return f"Неверные данные для удаления: {e}"

    row = cur.execute(f"SELECT * FROM {TABLE_BIRTHDAYS} WHERE rowid = (SELECT rowid FROM {TABLE_BIRTHDAYS} WHERE caller_id = {caller_id} ORDER BY birthday LIMIT 1 OFFSET {offset});").fetchone()
    if row is None:
        return f"Неверный номер для удаления: {offset}"

    len_before = len(get_birthdays(caller_id)[0])
    what = f"DELETE FROM birthdays WHERE rowid = (SELECT rowid FROM birthdays WHERE caller_id = {caller_id} ORDER BY birthday LIMIT 1 OFFSET {offset});"
    
    cur.execute(what)
    con.commit()
    len_after = len(get_birthdays(caller_id)[0])
    if len_before == len_after:
        return "ERR: unexpected len_before != len_after"
    return f"Удален день рождения {row[2]}"

def init_db_if_needed():
    global cur, con
    con = sql.connect(BIRTHDAYS_DB_FILE_PATH)
    cur = con.cursor()
    # https://sqlite.org/datatype3.html#date_and_time_datatype
    cur.execute(f"CREATE TABLE IF NOT EXISTS {TABLE_CALLERS}(caller_id INTEGER PRIMARY KEY, update_on_hour INTEGER)")
    cur.execute(f"CREATE TABLE IF NOT EXISTS {TABLE_BIRTHDAYS}(caller_id INTEGER, birthday DATE, comment TINYTEXT, last_notified_year INTEGER, FOREIGN KEY (caller_id) REFERENCES caller(caller_id))")
    con.commit()

def main():
    DEBUG_CALLER = "123456789"

    init_db_if_needed()

    user_input = ""
    while user_input != "exit":
        user_input = input()
        user_input_split = user_input.split(maxsplit=3)
        if len(user_input_split) == 0:
            continue
        cmd = user_input_split[0]
        if cmd == "get":
            print(get_all_birthdays())
        if cmd == "add" and len(user_input_split) == 3:
            print(add_birthday(DEBUG_CALLER, user_input_split[1], user_input_split[2]))
        if cmd == "del" and len(user_input_split) == 2:
            print(remove_birthday(DEBUG_CALLER, user_input_split[1]))
        if cmd == "act":
            count = len(get_birthdays(DEBUG_CALLER)[0])
            for i in range(count):
                actualize_birthday_last_notification(DEBUG_CALLER, i)
        if user_input == "exit":
            break

if __name__ == "__main__":
    main()