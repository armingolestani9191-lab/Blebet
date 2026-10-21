# ==========================================
# BaleBet - Users
# ==========================================

import time

from database import (
    get_connection,
    get_user_admin_info,
    find_user,
    save_user,
    is_user_banned
)


# ==========================================
# دریافت کاربر
# ==========================================

def get_user(user_id):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            user_id,
            username,
            first_name,
            tokens
        FROM users
        WHERE user_id = ?
        """,
        (
            user_id,
        )
    )

    user = cursor.fetchone()

    connection.close()

    return user


# ==========================================
# ساخت کاربر
# ==========================================

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


# ==========================================
# دریافت یا ساخت کاربر
# ==========================================

def get_or_create_user(
    user_id,
    username,
    first_name
):

    user = get_user(
        user_id
    )

    if user is None:

        create_user(
            user_id,
            username,
            first_name
        )

        user = get_user(
            user_id
        )

    else:

        # ==================================
        # بروزرسانی اطلاعات کاربر
        # ==================================

        connection = get_connection()

        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE users
            SET
                username = ?,
                first_name = ?
            WHERE user_id = ?
            """,
            (
                username,
                first_name,
                user_id
            )
        )

        connection.commit()

        connection.close()

        user = get_user(
            user_id
        )

    return user


# ==========================================
# فعالیت کاربر
# ==========================================

def update_activity(
    user_id
):

    now = int(
        time.time()
    )

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
        (
            user_id,
            now
        )
    )

    connection.commit()

    connection.close()


# ==========================================
# بررسی فعال بودن کاربر
# ==========================================

def get_active_users():

    five_minutes_ago = (
        int(time.time()) - 300
    )

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM user_activity
        WHERE last_activity >= ?
        """,
        (
            five_minutes_ago,
        )
    )

    result = cursor.fetchone()

    connection.close()

    if result is None:

        return 0

    return result[0]


# ==========================================
# دریافت اطلاعات کامل کاربر
# ==========================================

def get_user_info(
    user_id
):

    return get_user_admin_info(
        user_id
    )


# ==========================================
# جستجوی کاربر
# ==========================================

def search_user(
    query
):

    return find_user(
        query
    )


# ==========================================
# بررسی بن بودن
# ==========================================

def user_is_banned(
    user_id
):

    return is_user_banned(
        user_id
    )


# ==========================================
# بروزرسانی اطلاعات کاربر
# ==========================================

def update_user_info(
    user_id,
    username=None,
    first_name=None
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

    # ======================================
    # بررسی وجود کاربر
    # ======================================

    cursor.execute(
        """
        SELECT
            username,
            first_name
        FROM users
        WHERE user_id = ?
        """,
        (
            user_id,
        )
    )

    current = cursor.fetchone()

    if current is None:

        connection.close()

        return False

    current_username = current[0]
    current_first_name = current[1]

    if username is None:

        username = current_username

    if first_name is None:

        first_name = current_first_name

    # ======================================
    # بروزرسانی
    # ======================================

    cursor.execute(
        """
        UPDATE users
        SET
            username = ?,
            first_name = ?
        WHERE user_id = ?
        """,
        (
            username,
            first_name,
            user_id
        )
    )

    changed = (
        cursor.rowcount > 0
    )

    connection.commit()

    connection.close()

    return changed


# ==========================================
# بررسی وجود کاربر
# ==========================================

def exists(
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

    cursor.execute(
        """
        SELECT 1
        FROM users
        WHERE user_id = ?
        LIMIT 1
        """,
        (
            user_id,
        )
    )

    result = cursor.fetchone()

    connection.close()

    return result is not None


# ==========================================
# دریافت آیدی همه کاربران
# ==========================================

def get_all_users():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT user_id
        FROM users
        ORDER BY user_id
        """
    )

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

    cursor.execute(
        """
        SELECT user_id
        FROM users
        WHERE banned = 0
        ORDER BY user_id
        """
    )

    rows = cursor.fetchall()

    connection.close()

    return [
        row[0]
        for row in rows
    ]


# ==========================================
# تعداد کاربران
# ==========================================

def get_user_count():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM users
        """
    )

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

def get_banned_users_count():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM users
        WHERE banned = 1
        """
    )

    result = cursor.fetchone()

    connection.close()

    if result is None:

        return 0

    return int(
        result[0]
    )


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

    cursor.execute(
        """
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
        """,
        (
            limit,
        )
    )

    rows = cursor.fetchall()

    connection.close()

    return rows


# ==========================================
# دریافت کاربران اخیر
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

    cursor.execute(
        """
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
        """,
        (
            limit,
        )
    )

    rows = cursor.fetchall()

    connection.close()

    return rows


# ==========================================
# بروزرسانی فعالیت و اطلاعات کاربر
# ==========================================

def touch_user(
    user_id,
    username=None,
    first_name=None
):

    update_user_info(
        user_id,
        username,
        first_name
    )

    update_activity(
        user_id
    )


# ==========================================
# ثبت کاربر جدید و فعالیت
# ==========================================

def register_user(
    user_id,
    username,
    first_name
):

    user = get_or_create_user(
        user_id,
        username,
        first_name
    )

    update_activity(
        user_id
    )

    return user
