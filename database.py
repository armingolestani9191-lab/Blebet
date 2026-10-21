# ==========================================
# BaleBet - Database
# ==========================================

import os
import sqlite3

from config import DATABASE_PATH


# ==========================================
# اتصال به دیتابیس
# ==========================================

def get_connection():

    folder = os.path.dirname(
        DATABASE_PATH
    )

    if folder:

        os.makedirs(
            folder,
            exist_ok=True
        )

    return sqlite3.connect(
        DATABASE_PATH,
        timeout=10
    )


# ==========================================
# ساخت دیتابیس
# ==========================================

def init_database():

    connection = get_connection()
    cursor = connection.cursor()

    # ======================================
    # کاربران
    # ======================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            tokens INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ======================================
    # فعالیت کاربران
    # ======================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_activity (
            user_id INTEGER PRIMARY KEY,
            last_activity INTEGER NOT NULL
        )
    """)

    # ======================================
    # دعوت‌ها
    # ======================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS referrals (
            referred_user_id INTEGER PRIMARY KEY,
            referrer_user_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ======================================
    # تراکنش‌های ژتون
    # ======================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS token_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            reason TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()

    connection.close()


# ==========================================
# دریافت تمام کاربران
# ==========================================

def get_all_user_ids():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT user_id
        FROM users
        ORDER BY user_id
    """)

    rows = cursor.fetchall()

    connection.close()

    return [
        row[0]
        for row in rows
    ]


# ==========================================
# تعداد کل کاربران
# ==========================================

def get_user_count():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM users
    """)

    result = cursor.fetchone()

    connection.close()

    if result is None:

        return 0

    return int(
        result[0]
    )


# ==========================================
# مجموع ژتون کاربران
# ==========================================

def get_total_tokens():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT COALESCE(
            SUM(tokens),
            0
        )
        FROM users
    """)

    result = cursor.fetchone()

    connection.close()

    if result is None:

        return 0

    return int(
        result[0]
    )


# ==========================================
# تعداد دعوت‌های موفق
# ==========================================

def get_referral_count():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM referrals
    """)

    result = cursor.fetchone()

    connection.close()

    if result is None:

        return 0

    return int(
        result[0]
    )


# ==========================================
# دریافت اطلاعات یک کاربر برای ادمین
# ==========================================

def get_user_admin_info(
    user_id
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            user_id,
            username,
            first_name,
            tokens,
            created_at
        FROM users
        WHERE user_id = ?
    """, (
        user_id,
    ))

    result = cursor.fetchone()

    connection.close()

    if result is None:

        return None

    return {
        "user_id": result[0],
        "username": result[1],
        "first_name": result[2],
        "tokens": result[3],
        "created_at": result[4]
    }


# ==========================================
# تغییر موجودی کاربر توسط ادمین
# ==========================================

def set_user_tokens(
    user_id,
    amount
):

    try:

        amount = int(
            amount
        )

    except (
        TypeError,
        ValueError
    ):

        return False

    if amount < 0:

        return False

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE users
        SET tokens = ?
        WHERE user_id = ?
    """, (
        amount,
        user_id
    ))

    if cursor.rowcount == 0:

        connection.rollback()
        connection.close()

        return False

    connection.commit()
    connection.close()

    return True


# ==========================================
# افزودن / کم کردن ژتون ادمینی
# ==========================================

def change_user_tokens(
    user_id,
    amount,
    reason="تغییر توسط ادمین"
):

    try:

        amount = int(
            amount
        )

    except (
        TypeError,
        ValueError
    ):

        return False

    if amount == 0:

        return False

    connection = get_connection()
    cursor = connection.cursor()

    # ======================================
    # اگر برداشت است
    # ======================================

    if amount < 0:

        cursor.execute("""
            UPDATE users
            SET tokens = tokens + ?
            WHERE user_id = ?
            AND tokens >= ?
        """, (
            amount,
            user_id,
            abs(amount)
        ))

    else:

        cursor.execute("""
            UPDATE users
            SET tokens = tokens + ?
            WHERE user_id = ?
        """, (
            amount,
            user_id
        ))

    # ======================================
    # کاربر پیدا نشد
    # ======================================

    if cursor.rowcount == 0:

        connection.rollback()
        connection.close()

        return False

    # ======================================
    # ثبت تراکنش
    # ======================================

    cursor.execute("""
        INSERT INTO token_transactions (
            user_id,
            amount,
            reason
        )
        VALUES (?, ?, ?)
    """, (
        user_id,
        amount,
        reason
    ))

    connection.commit()

    connection.close()

    return True


# ==========================================
# دریافت تراکنش‌های کاربر
# ==========================================

def get_user_transactions(
    user_id,
    limit=20
):

    try:

        limit = int(
            limit
        )

    except (
        TypeError,
        ValueError
    ):

        limit = 20

    if limit <= 0:

        limit = 20

    if limit > 100:

        limit = 100

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            amount,
            reason,
            created_at
        FROM token_transactions
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT ?
    """, (
        user_id,
        limit
    ))

    rows = cursor.fetchall()

    connection.close()

    return rows


# ==========================================
# دریافت کاربران برای همگانی
# ==========================================

def get_broadcast_users():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT user_id
        FROM users
        WHERE user_id IS NOT NULL
        ORDER BY user_id
    """)

    rows = cursor.fetchall()

    connection.close()

    return [
        row[0]
        for row in rows
    ]


# ==========================================
# حذف کاربر
# ==========================================

def delete_user(
    user_id
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM user_activity
        WHERE user_id = ?
    """, (
        user_id,
    ))

    cursor.execute("""
        DELETE FROM users
        WHERE user_id = ?
    """, (
        user_id,
    ))

    deleted = cursor.rowcount

    connection.commit()

    connection.close()

    return deleted > 0