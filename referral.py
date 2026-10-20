# ==========================================
# BaleBet - Referral System
# ==========================================

from database import get_connection
from config import (
    REFERRER_REWARD,
    REFERRED_REWARD
)

from wallet import add_tokens


def create_referral(
    referrer_id,
    referred_id
):

    # دعوت خود شخص
    if referrer_id == referred_id:

        return False

    connection = get_connection()

    cursor = connection.cursor()

    # آیا قبلاً دعوت شده؟
    cursor.execute(
        """
        SELECT referred_user_id
        FROM referrals
        WHERE referred_user_id = ?
        """,
        (referred_id,)
    )

    existing = cursor.fetchone()

    if existing:

        connection.close()

        return False

    # بررسی وجود دعوت‌کننده
    cursor.execute(
        """
        SELECT user_id
        FROM users
        WHERE user_id = ?
        """,
        (referrer_id,)
    )

    referrer = cursor.fetchone()

    if referrer is None:

        connection.close()

        return False

    # ثبت دعوت
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

    # جایزه دعوت‌کننده
    if REFERRER_REWARD > 0:

        add_tokens(
            referrer_id,
            REFERRER_REWARD,
            "🎁 پاداش دعوت دوست"
        )

    # جایزه کاربر جدید
    if REFERRED_REWARD > 0:

        add_tokens(
            referred_id,
            REFERRED_REWARD,
            "🎁 پاداش ورود با لینک دعوت"
        )

    return True


def get_referral_count(user_id):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM referrals
        WHERE referrer_user_id = ?
        """,
        (user_id,)
    )

    result = cursor.fetchone()

    connection.close()

    if result is None:

        return 0

    return result[0]
