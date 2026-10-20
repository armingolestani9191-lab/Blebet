# ==========================================
# BaleBet - Games
# ==========================================

import random

from config import (
    SPIN_COST,
    SPIN_REWARDS
)

from wallet import (
    get_balance,
    remove_tokens,
    add_tokens
)


def validate_spin_rewards():

    total = sum(
        float(item["chance"])
        for item in SPIN_REWARDS
    )

    return abs(total - 100) < 0.000001


def spin_wheel(user_id):

    # بررسی تنظیمات
    if not validate_spin_rewards():

        return {
            "success": False,
            "message": "تنظیمات احتمال‌های چرخونه اشتباهه."
        }

    # بررسی موجودی
    balance = get_balance(user_id)

    if balance < SPIN_COST:

        return {
            "success": False,
            "message": (
                "❌ ژتون کافی نداری.\n\n"
                f"🪙 هزینه چرخونه: "
                f"<b>{SPIN_COST:,}</b> ژتون\n"
                f"🪙 موجودی شما: "
                f"<b>{balance:,}</b> ژتون"
            )
        }

    # دریافت هزینه
    removed = remove_tokens(
        user_id,
        SPIN_COST,
        "🎡 هزینه چرخونه"
    )

    if not removed:

        return {
            "success": False,
            "message": "❌ انجام چرخونه ممکن نشد."
        }

    # انتخاب جایزه
    rewards = list(SPIN_REWARDS)

    weights = [
        float(item["chance"])
        for item in rewards
    ]

    result = random.choices(
        rewards,
        weights=weights,
        k=1
    )[0]

    reward = int(
        result["reward"]
    )

    # پرداخت جایزه
    if reward > 0:

        add_tokens(
            user_id,
            reward,
            f"🎡 جایزه چرخونه: {reward} ژتون"
        )

    return {
        "success": True,
        "name": result["name"],
        "reward": reward,
        "cost": SPIN_COST
    }
