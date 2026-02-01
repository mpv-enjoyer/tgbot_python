import sqlite3 as sql
sql.threadsafety = 3 # https://docs.python.org/3/library/sqlite3.html#sqlite3.threadsafety
import os
import datetime

BIRTHDAYS_DB_FILE_PATH = "birthdays.db"
LIMIT_BIRTHDAYS_PER_CALLER = 50

# Returns list(caller_id, birthday, comment)
def get_birthdays(cur: sql.Cursor, ):
    res = cur.execute("SELECT * FROM birthdays WHERE name='spam'")

def main():
    db_existed = os.path.exists(BIRTHDAYS_DB_FILE_PATH)
    con = sql.connect(BIRTHDAYS_DB_FILE_PATH)
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS birthdays(caller_id TINYTEXT, birthday DATE NOT NULL, comment TINYTEXT)")

    user_input = ""
    while user_input != "exit":
        user_input = input()
        user_input_split = user_input.split(maxsplit=2)
        if len(user_input_split) < 3:
            continue
        cmd = user_input_split[0]
        date = user_input_split[1]
        comment = user_input_split[2]


"""
   FOREIGN KEY (contact_id) 
      REFERENCES contacts (contact_id) 
         ON DELETE CASCADE 
         ON UPDATE NO ACTION,
"""