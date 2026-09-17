import sqlite3

from settings import settings


class DB_Error(Exception):
    def __init__(self, message: str, *args):
        super().__init__(*args)
        self.message = message
        
        print(message)



def init_db():
    USERS_DB_NAME = settings.USERS_DB_NAME
    try:
        with sqlite3.connect(USERS_DB_NAME) as users:
            cursor = users.cursor()

            cursor.execute("""CREATE TABLE IF NOT EXISTS Users (
                            id INTEGER PRIMARY KEY,
                            login TEXT NOT NULL UNIQUE,
                            password_hash TEXT NOT NULL,
                            role TEXT NOT NULL,
                            reg_date TEXT NOT NULL,
                            token_version INTEGER DEFAULT 1,
                            comment TEXT
                            )""")
        
            cursor.execute("""CREATE TABLE IF NOT EXISTS known_IPs (
                           id INTEGER PRIMARY KEY,
                           user_id INTEGER NOT NULL,
                           ip TEXT NOT NULL,
                           is_active INTEGER NOT NULL,
                           last_checked INTEGER,
                           UNIQUE(user_id, ip)
                           )""")
                           
            cursor.execute("SELECT COUNT(*) FROM Users")
            if cursor.fetchone()[0] == 0:
                cursor.execute(
                    "INSERT INTO Users (login, password_hash, role, reg_date, comment) VALUES (?, ?, ?, ?, ?)",
                    (
                        "login0",
                        "password_hash0",
                        "user",
                        "yyyy-mm-dd",
                        "Template",
                    ),
                )
        
            users.commit()
    except sqlite3.Error as e:
        raise DB_Error("Ошибка при инициализации БД")