import sqlite3 as sql
sql.threadsafety = 3 # https://docs.python.org/3/library/sqlite3.html#sqlite3.threadsafety
import os
import datetime

TABLE_CALLERS = "callers"
TABLE_BIRTHDAYS = "birthdays"
BIRTHDAYS_DB_FILE_PATH = "birthdays.db"
LIMIT_BIRTHDAYS_PER_CALLER = 50
DEBUG_CALLER = "123456789"
DATE_FORMAT = "%d.%m.%y"
TIME_FORMAT = "%H"
SQL_DATE_FORMAT = "%Y-%m-%d"

# Returns list(caller_id, birthday, comment)
def get_birthdays(cur: sql.Cursor, caller_id: int):
    res = cur.execute(f"SELECT * FROM {TABLE_BIRTHDAYS} WHERE caller_id=?", (caller_id,)).fetchall()
    res2 = cur.execute(f"SELECT update_on FROM {TABLE_CALLERS} WHERE caller_id=?", (caller_id,)).fetchone()
    return res, res2

def add_birthday(con: sql.Connection, cur: sql.Cursor, caller_id: str, date: str, comment: str):
    try:
        sql_date = datetime.datetime.strptime(date, DATE_FORMAT).strftime(SQL_DATE_FORMAT)
        caller_id = int(caller_id)
    except Exception as e:
        print(f"strptime or caller_id thrown: {e}")
        return

    if cur.execute(f"SELECT * FROM {TABLE_CALLERS} WHERE caller_id={caller_id}").fetchone() is None:
        DEFAULT_NOTIFICATION_TIME = 12
        cur.execute(f"INSERT INTO {TABLE_CALLERS} VALUES (?, ?)", (caller_id, DEFAULT_NOTIFICATION_TIME))

    cur.execute(f"INSERT INTO {TABLE_BIRTHDAYS} VALUES (?, ?, ?)", (caller_id, sql_date, comment))
    con.commit()
    print("inserted.")

def remove_birthday(con: sql.Connection, cur: sql.Cursor, caller_id: str, offset: str):
    try:
        offset = int(offset)
        caller_id = int(caller_id)
    except Exception as e:
        print(f"offset or caller_id thrown: {e}")
        return
    
    # what = f"DELETE FROM {TABLE_BIRTHDAYS} WHERE caller_id = {caller_id} LIMIT 1 OFFSET {offset}"
    what = f"DELETE FROM birthdays WHERE rowid = (SELECT rowid FROM birthdays WHERE caller_id = {caller_id} ORDER BY birthday LIMIT 1 OFFSET {offset});"
    cur.execute(what)
    con.commit()
    print("removed if existed.")

def init_db_if_needed(con: sql.Connection, cur: sql.Cursor):
    # https://sqlite.org/datatype3.html#date_and_time_datatype
    cur.execute(f"CREATE TABLE IF NOT EXISTS {TABLE_CALLERS}(caller_id INTEGER PRIMARY KEY, update_on INTEGER)")
    cur.execute(f"CREATE TABLE IF NOT EXISTS {TABLE_BIRTHDAYS}(caller_id INTEGER, birthday DATE, comment TINYTEXT, FOREIGN KEY (caller_id) REFERENCES caller(caller_id))")
    con.commit()

def main():
    db_existed = os.path.exists(BIRTHDAYS_DB_FILE_PATH)
    con = sql.connect(BIRTHDAYS_DB_FILE_PATH)
    cur = con.cursor()
    init_db_if_needed(con, cur)

    user_input = ""
    while user_input != "exit":
        user_input = input()
        user_input_split = user_input.split(maxsplit=3)
        if len(user_input_split) == 0:
            continue
        cmd = user_input_split[0]
        if cmd == "get":
            print(get_birthdays(cur, DEBUG_CALLER))
        if cmd == "add" and len(user_input_split) == 3:
            add_birthday(con, cur, DEBUG_CALLER, user_input_split[1], user_input_split[2])
        if cmd == "del" and len(user_input_split) == 2:
            remove_birthday(con, cur, DEBUG_CALLER, user_input_split[1])
        if user_input == "exit":
            break

if __name__ == "__main__":
    main()