# ==========================================
# BaleBet - Wallet
# ==========================================

from database import (
    get_connection,
    get_user_tokens,
    change_user_tokens,
    set_user_tokens,
    get_user_transactions,
)


# ==========================================
# دریافت موجودی کاربر
# ==========================================

def get_balance(user_id):

    return get_user_tokens(
        user_id
    )


# ==========================================
# افزایش موجودی
# ==========================================

def add_tokens(
    user_id,
    amount,
    reason="افزایش موجودی"
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

    if amount <= 0:
        return False

    return change_user_tokens(
        user_id,
        amount,
        reason
    )


# ==========================================
# کاهش موجودی
# ==========================================

def remove_tokens(
    user_id,
    amount,
    reason="کاهش موجودی"
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

    if amount <= 0:
        return False

    return change_user_tokens(
        user_id,
        -amount,
        reason
    )


# ==========================================
# تغییر موجودی توسط ادمین
# ==========================================

def admin_change_balance(
    user_id,
    amount,
    reason="تغییر موجودی توسط ادمین"
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

    return change_user_tokens(
        user_id,
        amount,
        reason
    )


# ==========================================
# تعیین موجودی توسط ادمین
# ==========================================

def admin_set_balance(
    user_id,
    amount,
    reason="تنظیم موجودی توسط ادمین"
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

    return set_user_tokens(
        user_id,
        amount,
        reason
    )


# ==========================================
# بررسی موجودی کافی
# ==========================================

def has_enough_tokens(
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

    balance = get_balance(
        user_id
    )

    if balance is None:
        return False

    return balance >= amount


# ==========================================
# خرج کردن ژتون
# ==========================================

def spend_tokens(
    user_id,
    amount,
    reason="خرج ژتون"
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

    if amount <= 0:
        return False

    return change_user_tokens(
        user_id,
        -amount,
        reason
    )


# ==========================================
# دریافت تراکنش‌های کاربر
# ==========================================

def get_transactions(
    user_id,
    limit=20
):

    return get_user_transactions(
        user_id,
        limit
    )


# ==========================================
# دریافت موجودی برای پنل ادمین
# ==========================================

def get_admin_balance(
    user_id
):

    return get_balance(
        user_id
    )


# ==========================================
# افزایش موجودی توسط پنل
# ==========================================

def admin_add_tokens(
    user_id,
    amount
):

    return admin_change_balance(
        user_id,
        amount,
        "افزایش موجودی توسط پنل ادمین"
    )


# ==========================================
# کاهش موجودی توسط پنل
# ==========================================

def admin_remove_tokens(
    user_id,
    amount
):

    return admin_change_balance(
        user_id,
        -abs(
            int(amount)
        ),
        "کاهش موجودی توسط پنل ادمین"
    )


# ==========================================
# تنظیم مستقیم موجودی توسط پنل
# ==========================================

def admin_set_tokens(
    user_id,
    amount
):

    return admin_set_balance(
        user_id,
        amount,
        "تنظیم موجودی توسط پنل ادمین"
    )
