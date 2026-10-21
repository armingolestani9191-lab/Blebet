# ==========================================
# BaleBet - Wallet
# ==========================================

from database import get_connection
from config import TOKEN_VALUE


# ==========================================
# دریافت موجودی
# ==========================================

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


# ==========================================
# دریافت ارزش موجودی
# ==========================================

def get_balance_value(tokens):

    return tokens * TOKEN_VALUE


# ==========================================
# دریافت قیمت فعلی ژتون
# ==========================================

def get_token_value():

    return TOKEN_VALUE


# ==========================================
# تغییر قیمت ژتون در زمان اجرا
# ==========================================

def set_token_value(value):

    global TOKEN_VALUE

    try:

        value = int(value)

    except (
        TypeError,
        ValueError
    ):

        return False

    if value <= 0:

        return False

    TOKEN_VALUE = value

    return True


# ==========================================
# افزودن ژتون
# ==========================================

def add_tokens(
    user_id,
    amount,
    reason="دریافت ژتون"
):

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
        (
            amount,
            user_id
        )
    )

    if cursor.rowcount == 0:

        connection.rollback()

        connection.close()

        return False

    cursor.execute(
        """
        INSERT INTO token_transactions (
            user_id,
            amount,
            reason
        )
        VALUES (?, ?, ?)
        """,
        (
            user_id,
            amount,
            reason
        )
    )

    connection.commit()

    connection.close()

    return True


# ==========================================
# حذف ژتون
# ==========================================

def remove_tokens(
    user_id,
    amount,
    reason="مصرف ژتون"
):

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
        (
            amount,
            user_id,
            amount
        )
    )

    if cursor.rowcount == 0:

        connection.rollback()

        connection.close()

        return False

    cursor.execute(
        """
        INSERT INTO token_transactions (
            user_id,
            amount,
            reason
        )
        VALUES (?, ?, ?)
        """,
        (
            user_id,
            -amount,
            reason
        )
    )

    connection.commit()

    connection.close()

    return True


# ==========================================
# تنظیم مستقیم موجودی کاربر
# مخصوص پنل ادمین
# ==========================================

def set_balance(
    user_id,
    amount,
    reason="تنظیم موجودی توسط ادمین"
):

    try:

        amount = int(amount)

    except (
        TypeError,
        ValueError
    ):

        return False

    if amount < 0:

        return False

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT tokens
        FROM users
        WHERE user_id = ?
        """,
        (
            user_id,
        )
    )

    result = cursor.fetchone()

    if result is None:

        connection.close()

        return False

    old_balance = result[0]

    difference = amount - old_balance

    cursor.execute(
        """
        UPDATE users
        SET tokens = ?
        WHERE user_id = ?
        """,
        (
            amount,
            user_id
        )
    )

    if difference != 0:

        cursor.execute(
            """
            INSERT INTO token_transactions (
                user_id,
                amount,
                reason
            )
            VALUES (?, ?, ?)
            """,
            (
                user_id,
                difference,
                reason
            )
        )

    connection.commit()

    connection.close()

    return True


# ==========================================
# افزودن ژتون توسط ادمین
# ==========================================

def admin_add_tokens(
    user_id,
    amount
):

    try:

        amount = int(amount)

    except (
        TypeError,
        ValueError
    ):

        return False

    if amount <= 0:

        return False

    return add_tokens(
        user_id,
        amount,
        "👑 افزایش موجودی توسط ادمین"
    )


# ==========================================
# کم کردن ژتون توسط ادمین
# ==========================================

def admin_remove_tokens(
    user_id,
    amount
):

    try:

        amount = int(amount)

    except (
        TypeError,
        ValueError
    ):

        return False

    if amount <= 0:

        return False

    return remove_tokens(
        user_id,
        amount,
        "👑 کاهش موجودی توسط ادمین"
    )