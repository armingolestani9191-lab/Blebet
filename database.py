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

    connection = sqlite3.connect(
        DATABASE_PATH,
        timeout=30
    )

    connection.execute(
        "PRAGMA journal_mode=WAL"
    )

    connection.execute(
        "PRAGMA busy_timeout=30000"
    )

    return connection


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
            banned INTEGER NOT NULL DEFAULT 0,
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

    # ======================================
    # تنظیمات ربات
    # ======================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bot_settings (
            setting_name TEXT PRIMARY KEY,
            setting_value TEXT NOT NULL
        )
    """)

    # ======================================
    # کانال‌های جوین اجباری
    # ======================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS force_join_channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ======================================
    # Migration برای دیتابیس‌های قدیمی
    # ======================================

    cursor.execute("""
        PRAGMA table_info(users)
    """)

    columns = [
        row[1]
        for row in cursor.fetchall()
    ]

    if "banned" not in columns:

        cursor.execute("""
            ALTER TABLE users
            ADD COLUMN banned INTEGER NOT NULL DEFAULT 0
        """)

    # ======================================
    # ایندکس‌ها برای سرعت
    # ======================================

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_users_username
        ON users(username)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_users_banned
        ON users(banned)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_user_activity_last
        ON user_activity(last_activity)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_transactions_user
        ON token_transactions(user_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_referrals_referrer
        ON referrals(referrer_user_id)
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
# دریافت کاربران برای همگانی
# ==========================================

def get_broadcast_users():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT user_id
        FROM users
        WHERE user_id IS NOT NULL
        AND banned = 0
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
# تعداد کاربران بن شده
# ==========================================

def get_banned_user_count():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM users
        WHERE banned = 1
    """)

    result = cursor.fetchone()

    connection.close()

    if result is None:
        return 0

    return int(
        result[0]
    )


# ==========================================
# تعداد کاربران عادی
# ==========================================

def get_active_user_count():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM users
        WHERE banned = 0
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
        WHERE banned = 0
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
# دریافت اطلاعات یک کاربر
# ==========================================

def get_user_admin_info(
    user_id
):

    try:
        user_id = int(
            user_id
        )

    except (
        TypeError,
        ValueError
    ):
        return None

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            user_id,
            username,
            first_name,
            tokens,
            banned,
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
        "banned": bool(result[4]),
        "created_at": result[5]
    }


# ==========================================
# جستجوی کاربر با آیدی یا یوزرنیم
# ==========================================

def find_user(
    query
):

    if query is None:
        return None

    query = str(
        query
    ).strip()

    if not query:
        return None

    connection = get_connection()
    cursor = connection.cursor()

    if query.lstrip("-").isdigit():

        try:
            user_id = int(
                query
            )

        except ValueError:
            connection.close()
            return None

        cursor.execute("""
            SELECT
                user_id,
                username,
                first_name,
                tokens,
                banned,
                created_at
            FROM users
            WHERE user_id = ?
            LIMIT 1
        """, (
            user_id,
        ))

    else:

        username = query.lstrip("@").strip()

        cursor.execute("""
            SELECT
                user_id,
                username,
                first_name,
                tokens,
                banned,
                created_at
            FROM users
            WHERE LOWER(username) = LOWER(?)
            LIMIT 1
        """, (
            username,
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
        "banned": bool(result[4]),
        "created_at": result[5]
    }


# ==========================================
# جستجوی چند کاربر
# ==========================================

def search_users(
    query,
    limit=20
):

    if query is None:
        return []

    query = str(
        query
    ).strip()

    if not query:
        return []

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

    username = query.lstrip("@")

    connection = get_connection()
    cursor = connection.cursor()

    if query.lstrip("-").isdigit():

        user_id = int(
            query
        )

        cursor.execute("""
            SELECT
                user_id,
                username,
                first_name,
                tokens,
                banned,
                created_at
            FROM users
            WHERE user_id = ?
            LIMIT ?
        """, (
            user_id,
            limit
        ))

    else:

        cursor.execute("""
            SELECT
                user_id,
                username,
                first_name,
                tokens,
                banned,
                created_at
            FROM users
            WHERE
                username LIKE ?
                OR first_name LIKE ?
            ORDER BY user_id DESC
            LIMIT ?
        """, (
            f"%{username}%",
            f"%{query}%",
            limit
        ))

    rows = cursor.fetchall()

    connection.close()

    return [
        {
            "user_id": row[0],
            "username": row[1],
            "first_name": row[2],
            "tokens": row[3],
            "banned": bool(row[4]),
            "created_at": row[5]
        }
        for row in rows
    ]


# ==========================================
# بررسی بن بودن کاربر
# ==========================================

def is_user_banned(
    user_id
):

    try:
        user_id = int(
            user_id
        )

    except (
        TypeError,
        ValueError
    ):
        return False

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT banned
        FROM users
        WHERE user_id = ?
    """, (
        user_id,
    ))

    result = cursor.fetchone()

    connection.close()

    if result is None:
        return False

    return bool(
        result[0]
    )


# ==========================================
# بن کردن کاربر
# ==========================================

def ban_user(
    user_id
):

    try:
        user_id = int(
            user_id
        )

    except (
        TypeError,
        ValueError
    ):
        return False

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE users
        SET banned = 1
        WHERE user_id = ?
    """, (
        user_id,
    ))

    changed = (
        cursor.rowcount > 0
    )

    if changed:
        connection.commit()
    else:
        connection.rollback()

    connection.close()

    return changed


# ==========================================
# آن‌بن کردن کاربر
# ==========================================

def unban_user(
    user_id
):

    try:
        user_id = int(
            user_id
        )

    except (
        TypeError,
        ValueError
    ):
        return False

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE users
        SET banned = 0
        WHERE user_id = ?
    """, (
        user_id,
    ))

    changed = (
        cursor.rowcount > 0
    )

    if changed:
        connection.commit()
    else:
        connection.rollback()

    connection.close()

    return changed


# ==========================================
# تغییر وضعیت بن
# ==========================================

def set_user_banned(
    user_id,
    banned
):

    if banned:
        return ban_user(
            user_id
        )

    return unban_user(
        user_id
    )


# ==========================================
# تغییر کامل موجودی کاربر
# ==========================================

def set_user_tokens(
    user_id,
    amount,
    reason="تنظیم موجودی توسط ادمین"
):

    try:
        user_id = int(
            user_id
        )

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
        SELECT tokens
        FROM users
        WHERE user_id = ?
    """, (
        user_id,
    ))

    result = cursor.fetchone()

    if result is None:

        connection.close()

        return False

    old_amount = int(
        result[0]
    )

    cursor.execute("""
        UPDATE users
        SET tokens = ?
        WHERE user_id = ?
    """, (
        amount,
        user_id
    ))

    difference = (
        amount - old_amount
    )

    if difference != 0:

        cursor.execute("""
            INSERT INTO token_transactions (
                user_id,
                amount,
                reason
            )
            VALUES (?, ?, ?)
        """, (
            user_id,
            difference,
            reason
        ))

    connection.commit()
    connection.close()

    return True


# ==========================================
# افزودن / کم کردن ژتون
# ==========================================

def change_user_tokens(
    user_id,
    amount,
    reason="تغییر توسط ادمین"
):

    try:
        user_id = int(
            user_id
        )

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

    if amount > 0:

        cursor.execute("""
            UPDATE users
            SET tokens = tokens + ?
            WHERE user_id = ?
        """, (
            amount,
            user_id
        ))

    else:

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

    if cursor.rowcount == 0:

        connection.rollback()
        connection.close()

        return False

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
# دریافت موجودی کاربر
# ==========================================

def get_user_tokens(
    user_id
):

    try:
        user_id = int(
            user_id
        )

    except (
        TypeError,
        ValueError
    ):
        return None

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT tokens
        FROM users
        WHERE user_id = ?
    """, (
        user_id,
    ))

    result = cursor.fetchone()

    connection.close()

    if result is None:
        return None

    return int(
        result[0]
    )


# ==========================================
# دریافت تراکنش‌های کاربر
# ==========================================

def get_user_transactions(
    user_id,
    limit=20
):

    try:
        user_id = int(
            user_id
        )

    except (
        TypeError,
        ValueError
    ):
        return []

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
# ثبت کاربر
# ==========================================

def save_user(
    user_id,
    username=None,
    first_name=""
):

    try:
        user_id = int(
            user_id
        )

    except (
        TypeError,
        ValueError
    ):
        return False

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO users (
            user_id,
            username,
            first_name
        )
        VALUES (?, ?, ?)
        ON CONFLICT(user_id)
        DO UPDATE SET
            username = excluded.username,
            first_name = excluded.first_name
    """, (
        user_id,
        username,
        first_name
    ))

    connection.commit()
    connection.close()

    return True


# ==========================================
# حذف کاربر
# ==========================================

def delete_user(
    user_id
):

    try:
        user_id = int(
            user_id
        )

    except (
        TypeError,
        ValueError
    ):
        return False

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM user_activity
        WHERE user_id = ?
    """, (
        user_id,
    ))

    cursor.execute("""
        DELETE FROM referrals
        WHERE referred_user_id = ?
           OR referrer_user_id = ?
    """, (
        user_id,
        user_id
    ))

    cursor.execute("""
        DELETE FROM token_transactions
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

    deleted = (
        cursor.rowcount > 0
    )

    connection.commit()
    connection.close()

    return deleted


# ==========================================
# تنظیمات ربات
# ==========================================

def set_setting(
    name,
    value
):

    if name is None:
        return False

    name = str(
        name
    ).strip()

    if not name:
        return False

    if value is None:
        return False

    value = str(
        value
    )

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO bot_settings (
            setting_name,
            setting_value
        )
        VALUES (?, ?)
        ON CONFLICT(setting_name)
        DO UPDATE SET
            setting_value = excluded.setting_value
    """, (
        name,
        value
    ))

    connection.commit()
    connection.close()

    return True


# ==========================================
# دریافت تنظیمات
# ==========================================

def get_setting(
    name,
    default=None
):

    if name is None:
        return default

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT setting_value
        FROM bot_settings
        WHERE setting_name = ?
    """, (
        str(name),
    ))

    result = cursor.fetchone()

    connection.close()

    if result is None:
        return default

    return result[0]


# ==========================================
# دریافت تنظیمات عددی
# ==========================================

def get_int_setting(
    name,
    default=0
):

    value = get_setting(
        name,
        None
    )

    if value is None:
        return default

    try:
        return int(
            value
        )

    except (
        TypeError,
        ValueError
    ):
        return default


# ==========================================
# دریافت تنظیمات بولی
# ==========================================

def get_bool_setting(
    name,
    default=False
):

    value = get_setting(
        name,
        None
    )

    if value is None:
        return default

    return str(
        value
    ).lower() in (
        "1",
        "true",
        "yes",
        "on"
    )


# ==========================================
# حذف تنظیم
# ==========================================

def delete_setting(
    name
):

    if name is None:
        return False

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM bot_settings
        WHERE setting_name = ?
    """, (
        str(name),
    ))

    deleted = (
        cursor.rowcount > 0
    )

    connection.commit()
    connection.close()

    return deleted


# ==========================================
# کانال‌های جوین اجباری
# ==========================================

def get_force_join_channels():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT channel
        FROM force_join_channels
        ORDER BY id
    """)

    rows = cursor.fetchall()

    connection.close()

    return [
        row[0]
        for row in rows
    ]


# ==========================================
# بررسی وجود کانال
# ==========================================

def force_join_channel_exists(
    channel
):

    if channel is None:
        return False

    channel = str(
        channel
    ).strip()

    if not channel:
        return False

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT 1
        FROM force_join_channels
        WHERE LOWER(channel) = LOWER(?)
        LIMIT 1
    """, (
        channel,
    ))

    result = cursor.fetchone()

    connection.close()

    return result is not None


# ==========================================
# افزودن کانال جوین اجباری
# ==========================================

def add_force_join_channel(
    channel
):

    if channel is None:
        return False

    channel = str(
        channel
    ).strip()

    if not channel:
        return False

    if not channel.startswith("@"):
        channel = "@" + channel

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute("""
            INSERT INTO force_join_channels (
                channel
            )
            VALUES (?)
        """, (
            channel,
        ))

        connection.commit()

        return True

    except sqlite3.IntegrityError:

        connection.rollback()

        return False

    finally:

        connection.close()


# ==========================================
# حذف کانال جوین اجباری
# ==========================================

def remove_force_join_channel(
    channel
):

    if channel is None:
        return False

    channel = str(
        channel
    ).strip()

    if not channel:
        return False

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM force_join_channels
        WHERE LOWER(channel) = LOWER(?)
    """, (
        channel,
    ))

    deleted = (
        cursor.rowcount > 0
    )

    connection.commit()
    connection.close()

    return deleted


# ==========================================
# حذف کانال بر اساس ID
# ==========================================

def remove_force_join_channel_by_id(
    channel_id
):

    try:
        channel_id = int(
            channel_id
        )

    except (
        TypeError,
        ValueError
    ):
        return False

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM force_join_channels
        WHERE id = ?
    """, (
        channel_id,
    ))

    deleted = (
        cursor.rowcount > 0
    )

    connection.commit()
    connection.close()

    return deleted


# ==========================================
# وضعیت جوین اجباری
# ==========================================

def is_force_join_enabled():

    return get_bool_setting(
        "force_join_enabled",
        False
    )


# ==========================================
# تغییر وضعیت جوین اجباری
# ==========================================

def set_force_join_enabled(
    enabled
):

    return set_setting(
        "force_join_enabled",
        "1" if enabled else "0"
    )


# ==========================================
# تعداد کانال‌های جوین اجباری
# ==========================================

def get_force_join_count():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM force_join_channels
    """)

    result = cursor.fetchone()

    connection.close()

    if result is None:
        return 0

    return int(
        result[0]
    )


# ==========================================
# دریافت تعداد کاربران فعال
# ==========================================

def get_active_users():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM users
        WHERE banned = 0
    """)

    result = cursor.fetchone()

    connection.close()

    if result is None:
        return 0

    return int(
        result[0]
    )


# ==========================================
# دریافت آمار کامل
# ==========================================

def get_admin_stats():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM users
    """)

    users = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM users
        WHERE banned = 0
    """)

    active_users = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM users
        WHERE banned = 1
    """)

    banned_users = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COALESCE(
            SUM(tokens),
            0
        )
        FROM users
    """)

    tokens = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM referrals
    """)

    referrals = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM token_transactions
    """)

    transactions = cursor.fetchone()[0]

    connection.close()

    return {
        "users": int(users),
        "active_users": int(active_users),
        "banned_users": int(banned_users),
        "tokens": int(tokens),
        "referrals": int(referrals),
        "transactions": int(transactions)
    }


# ==========================================
# دریافت آخرین کاربران
# ==========================================

def get_recent_users(
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
            user_id,
            username,
            first_name,
            tokens,
            banned,
            created_at
        FROM users
        ORDER BY rowid DESC
        LIMIT ?
    """, (
        limit,
    ))

    rows = cursor.fetchall()

    connection.close()

    return [
        {
            "user_id": row[0],
            "username": row[1],
            "first_name": row[2],
            "tokens": row[3],
            "banned": bool(row[4]),
            "created_at": row[5]
        }
        for row in rows
    ]


# ==========================================
# دریافت کاربران بن شده
# ==========================================

def get_banned_users(
    limit=100
):

    try:
        limit = int(
            limit
        )

    except (
        TypeError,
        ValueError
    ):
        limit = 100

    if limit <= 0:
        limit = 100

    if limit > 500:
        limit = 500

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
        WHERE banned = 1
        ORDER BY user_id DESC
        LIMIT ?
    """, (
        limit,
    ))

    rows = cursor.fetchall()

    connection.close()

    return rows


# ==========================================
# بررسی وجود کاربر
# ==========================================

def user_exists(
    user_id
):

    try:
        user_id = int(
            user_id
        )

    except (
        TypeError,
        ValueError
    ):
        return False

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT 1
        FROM users
        WHERE user_id = ?
        LIMIT 1
    """, (
        user_id,
    ))

    result = cursor.fetchone()

    connection.close()

    return result is not None


# ==========================================
# دریافت تعداد دعوت‌های یک کاربر
# ==========================================

def get_user_referral_count(
    user_id
):

    try:
        user_id = int(
            user_id
        )

    except (
        TypeError,
        ValueError
    ):
        return 0

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM referrals
        WHERE referrer_user_id = ?
    """, (
        user_id,
    ))

    result = cursor.fetchone()

    connection.close()

    if result is None:
        return 0

    return int(
        result[0]
    )


# ==========================================
# دریافت معرف کاربر
# ==========================================

def get_user_referrer(
    user_id
):

    try:
        user_id = int(
            user_id
        )

    except (
        TypeError,
        ValueError
    ):
        return None

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT referrer_user_id
        FROM referrals
        WHERE referred_user_id = ?
        LIMIT 1
    """, (
        user_id,
    ))

    result = cursor.fetchone()

    connection.close()

    if result is None:
        return None

    return int(
        result[0]
    )


# ==========================================
# دریافت کاربران دعوت شده توسط یک کاربر
# ==========================================

def get_referred_users(
    user_id,
    limit=100
):

    try:
        user_id = int(
            user_id
        )

    except (
        TypeError,
        ValueError
    ):
        return []

    try:
        limit = int(
            limit
        )

    except (
        TypeError,
        ValueError
    ):
        limit = 100

    if limit <= 0:
        limit = 100

    if limit > 500:
        limit = 500

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            r.referred_user_id,
            u.username,
            u.first_name,
            r.created_at
        FROM referrals r
        LEFT JOIN users u
            ON u.user_id = r.referred_user_id
        WHERE r.referrer_user_id = ?
        ORDER BY r.created_at DESC
        LIMIT ?
    """, (
        user_id,
        limit
    ))

    rows = cursor.fetchall()

    connection.close()

    return rows


# ==========================================
# پایان فایل
# ==========================================