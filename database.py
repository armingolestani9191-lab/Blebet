# ==========================================
# BaleBet - Database
# ==========================================

import os
import sqlite3

from config import DATABASE_PATH


def get_connection():
    folder = os.path.dirname(DATABASE_PATH)

    if folder:
        os.makedirs(folder, exist_ok=True)

    return sqlite3.connect(
        DATABASE_PATH,
        timeout=10
    )


def init_database():

    connection = get_connection()
    cursor = connection.cursor()

    # کاربران
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            tokens INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # فعالیت کاربران
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_activity (
            user_id INTEGER PRIMARY KEY,
            last_activity INTEGER NOT NULL
        )
    """)

    connection.commit()
    connection.close()