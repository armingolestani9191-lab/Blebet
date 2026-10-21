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


# ==========================================
# اعتبارسنجی جوایز چرخونه
# ==========================================

def validate_spin_rewards():

    total = sum(
        float(item["chance"])
        for item in SPIN_REWARDS
    )

    return abs(total - 100) < 0.000001


# ==========================================
# دریافت تنظیمات چرخونه
# ==========================================

def get_spin_settings():

    return {
        "cost": SPIN_COST,
        "rewards": SPIN_REWARDS
    }


# ==========================================
# بررسی تنظیمات جایزه
# ==========================================

def validate_reward_list(rewards):

    if not isinstance(
        rewards,
        list
    ):

        return False

    if not rewards:

        return False

    total_chance = 0

    for item in rewards:

        if not isinstance(
            item,
            dict
        ):

            return False

        if (
            "name" not in item
            or "reward" not in item
            or "chance" not in item
        ):

            return False

        try:

            reward = int(
                item["reward"]
            )

            chance = float(
                item["chance"]
            )

        except (
            TypeError,
            ValueError
        ):

            return False

        if reward < 0:

            return False

        if chance < 0:

            return False

        total_chance += chance

    return abs(
        total_chance - 100
    ) < 0.000001


# ==========================================
# تغییر هزینه چرخونه
# ==========================================

def set_spin_cost(
    new_cost
):

    global SPIN_COST

    try:

        new_cost = int(
            new_cost
        )

    except (
        TypeError,
        ValueError
    ):

        return False

    if new_cost <= 0:

        return False

    SPIN_COST = new_cost

    return True


# ==========================================
# تغییر جوایز چرخونه
# ==========================================

def set_spin_rewards(
    rewards
):

    global SPIN_REWARDS

    if not validate_reward_list(
        rewards
    ):

        return False

    SPIN_REWARDS = rewards

    return True


# ==========================================
# تغییر یک جایزه مشخص
# ==========================================

def update_spin_reward(
    index,
    name=None,
    reward=None,
    chance=None
):

    global SPIN_REWARDS

    try:

        index = int(
            index
        )

    except (
        TypeError,
        ValueError
    ):

        return False

    if (
        index < 0
        or index >= len(SPIN_REWARDS)
    ):

        return False

    new_rewards = [
        dict(item)
        for item in SPIN_REWARDS
    ]

    item = new_rewards[index]

    if name is not None:

        name = str(
            name
        ).strip()

        if not name:

            return False

        item["name"] = name

    if reward is not None:

        try:

            reward = int(
                reward
            )

        except (
            TypeError,
            ValueError
        ):

            return False

        if reward < 0:

            return False

        item["reward"] = reward

    if chance is not None:

        try:

            chance = float(
                chance
            )

        except (
            TypeError,
            ValueError
        ):

            return False

        if chance < 0:

            return False

        item["chance"] = chance

    if not validate_reward_list(
        new_rewards
    ):

        return False

    SPIN_REWARDS = new_rewards

    return True


# ==========================================
# چرخاندن چرخونه
# ==========================================

def spin_wheel(user_id):

    # بررسی تنظیمات
    if not validate_spin_rewards():

        return {
            "success": False,
            "message": "تنظیمات احتمال‌های چرخونه اشتباهه."
        }

    # بررسی موجودی
    balance = get_balance(
        user_id
    )

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
    rewards = list(
        SPIN_REWARDS
    )

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