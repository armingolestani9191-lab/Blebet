# ==========================================
# BaleBet - Referral System
# ==========================================

from database import (
    get_connection,
    get_setting,
    get_int_setting,
    set_setting,
)

import config

from wallet import add_tokens


# ==========================================
# تنظیمات پاداش
# ==========================================

REFERRER_REWARD = config.REFERRER_REWARD
REFERRED_REWARD = config.REFERRED_REWARD


# ==========================================
# دریافت پاداش دعوت‌کننده
# ==========================================

def get_referrer_reward():

    return get_int_setting(
        "referrer_reward",
        REFERRER_REWARD
    )


# ==========================================
# دریافت پاداش دعوت‌شونده
# ==========================================

def get_referred_reward():

    return get_int_setting(
        "referred_reward",
        REFERRED_REWARD
    )


# ==========================================
# دریافت تنظیمات Referral
# ==========================================

def get_referral_settings():

    return {
        "referrer_reward": get_referrer_reward(),
        "referred_reward": get_referred_reward()
    }


# ==========================================
# تغییر پاداش دعوت‌کننده
# ==========================================

def set_referrer_reward(
    amount
):

    global REFERRER_REWARD

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

    REFERRER_REWARD = amount

    return set_setting(
        "referrer_reward",
        amount
    )


# ==========================================
# تغییر پاداش دعوت‌شونده
# ==========================================

def set_referred_reward(
    amount
):

    global REFERRED_REWARD

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

    REFERRED_REWARD = amount

    return set_setting(
        "referred_reward",
        amount
    )


# ==========================================
# بررسی پاداش‌ها
# ==========================================

def validate_rewards():

    try:

        referrer_reward = get_referrer_reward()
        referred_reward = get_referred_reward()

        if referrer_reward < 0:

            return False

        if referred_reward < 0:

            return False

        return True

    except Exception:

        return False


# ==========================================
# ساخت دعوت
# ==========================================

def create_referral(
    referrer_id,
    referred_id
):

    # ======================================
    # دعوت خود شخص
    # ======================================

    if referrer_id == referred_id:

        return False

    # ======================================
    # بررسی تنظیمات
    # ======================================

    if not validate_rewards():

        return False

    # ======================================
    # دریافت پاداش‌های فعلی
    # ======================================

    referrer_reward = get_referrer_reward()
    referred_reward = get_referred_reward()

    connection = get_connection()

    cursor = connection.cursor()

    # ======================================
    # آیا قبلاً دعوت شده؟
    # ======================================

    cursor.execute(
        """
        SELECT referred_user_id
        FROM referrals
        WHERE referred_user_id = ?
        """,
        (
            referred_id,
        )
    )

    existing = cursor.fetchone()

    if existing:

        connection.close()

        return False

    # ======================================
    # بررسی وجود دعوت‌کننده
    # ======================================

    cursor.execute(
        """
        SELECT user_id
        FROM users
        WHERE user_id = ?
        """,
        (
            referrer_id,
        )
    )

    referrer = cursor.fetchone()

    if referrer is None:

        connection.close()

        return False

    # ======================================
    # ثبت دعوت
    # ======================================

    cursor.execute(
        """
        INSERT INTO referrals (
            referred_user_id,
            referrer_user_id
        )
        VALUES (?, ?)
        """,
        (
            referred_id,
            referrer_id
        )
    )

    connection.commit()

    connection.close()

    # ======================================
    # جایزه دعوت‌کننده
    # ======================================

    if referrer_reward > 0:

        add_tokens(
            referrer_id,
            referrer_reward,
            "🎁 پاداش دعوت دوست"
        )

    # ======================================
    # جایزه کاربر جدید
    # ======================================

    if referred_reward > 0:

        add_tokens(
            referred_id,
            referred_reward,
            "🎁 پاداش ورود با لینک دعوت"
        )

    return True


# ==========================================
# تعداد دعوت‌های موفق
# ==========================================

def get_referral_count(
    user_id
):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM referrals
        WHERE referrer_user_id = ?
        """,
        (
            user_id,
        )
    )

    result = cursor.fetchone()

    connection.close()

    if result is None:

        return 0

    return result[0]


# ==========================================
# دریافت دعوت‌های یک کاربر
# ==========================================

def get_user_referrals(
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

    cursor.execute(
        """
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
        """,
        (
            user_id,
            limit
        )
    )

    rows = cursor.fetchall()

    connection.close()

    return rows


# ==========================================
# دریافت معرف یک کاربر
# ==========================================

def get_referrer(
    referred_id
):

    try:

        referred_id = int(
            referred_id
        )

    except (
        TypeError,
        ValueError
    ):

        return None

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT referrer_user_id
        FROM referrals
        WHERE referred_user_id = ?
        LIMIT 1
        """,
        (
            referred_id,
        )
    )

    result = cursor.fetchone()

    connection.close()

    if result is None:

        return None

    return result[0]


# ==========================================
# بررسی اینکه کاربر قبلاً دعوت شده
# ==========================================

def has_referrer(
    user_id
):

    return get_referrer(
        user_id
    ) is not None


# ==========================================
# بررسی اینکه دعوت معتبر است
# ==========================================

def is_valid_referral(
    referrer_id,
    referred_id
):

    if referrer_id is None:
        return False

    if referred_id is None:
        return False

    try:

        referrer_id = int(
            referrer_id
        )

        referred_id = int(
            referred_id
        )

    except (
        TypeError,
        ValueError
    ):

        return False

    if referrer_id == referred_id:

        return False

    if has_referrer(
        referred_id
    ):

        return False

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT user_id
        FROM users
        WHERE user_id = ?
        LIMIT 1
        """,
        (
            referrer_id,
        )
    )

    result = cursor.fetchone()

    connection.close()

    return result is not None


# ==========================================
# دریافت مجموع پاداش یک دعوت‌کننده
# ==========================================

def get_referral_earnings(
    user_id
):

    count = get_referral_count(
        user_id
    )

    reward = get_referrer_reward()

    return count * reward
