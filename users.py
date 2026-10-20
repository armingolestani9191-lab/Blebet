# ==========================================
# BaleBet - Users
# ==========================================

import time

from database import get_connection


def get_user(user_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT user_id, username, first_name, tokens
        FROM users
        WHERE user_id = ?
        """,
        (user_id,)
    )

    user = cursor.fetchone()

    connection.close()

    return user


def create_user(
    user_id,
    username,
    first_name
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT OR IGNORE INTO users (
            user_id,
            username,
            first_name
        )
        VALUES (?, ?, ?)
        """,
        (
            user_id,
            username,
            first_name
        )
    )

    connection.commit()
    connection.close()


def get_or_create_user(
    user_id,
    username,
    first_name
):

    user = get_user(user_id)

    if user is None:

        create_user(
            user_id,
            username,
            first_name
        )

        user = get_user(user_id)

    return user


# ==========================================
# فعالیت کاربر
# ==========================================

def update_activity(user_id):

    now = int(time.time())

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO user_activity (
            user_id,
            last_activity
        )
        VALUES (?, ?)

        ON CONFLICT(user_id)
        DO UPDATE SET
            last_activity = excluded.last_activity
        """,
        (user_id, now)
    )

    connection.commit()
    connection.close()


def get_active_users():

    five_minutes_ago = int(time.time()) - 300

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM user_activity
        WHERE last_activity >= ?
        """,
        (five_minutes_ago,)
    )

    result = cursor.fetchone()

    connection.close()

    if result is None:
        return 0

    return result[0]