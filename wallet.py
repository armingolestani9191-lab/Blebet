# ==========================================
# BaleBet - Wallet
# ==========================================

from database import get_connection
from config import TOKEN_VALUE


def get_balance(user_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT tokens
        FROM users
        WHERE user_id = ?
        """,
        (user_id,)
    )

    result = cursor.fetchone()

    connection.close()

    if result is None:
        return 0

    return result[0]


def get_balance_value(tokens):
    return tokens * TOKEN_VALUE


def add_tokens(user_id, amount):
    if amount <= 0:
        return False

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE users
        SET tokens = tokens + ?
        WHERE user_id = ?
        """,
        (amount, user_id)
    )

    success = cursor.rowcount > 0

    connection.commit()
    connection.close()

    return success


def remove_tokens(user_id, amount):
    if amount <= 0:
        return False

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE users
        SET tokens = tokens - ?
        WHERE user_id = ?
        AND tokens >= ?
        """,
        (amount, user_id, amount)
    )

    success = cursor.rowcount > 0

    connection.commit()
    connection.close()

    return success