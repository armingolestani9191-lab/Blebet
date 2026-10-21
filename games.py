# ==========================================
# BaleBet - Games
# ==========================================

import json
import random

import config

from database import (
    get_setting,
    get_int_setting,
    set_setting
)

from wallet import (
    get_balance,
    remove_tokens,
    add_tokens
)


# ==========================================
# تنظیمات چرخونه
# ==========================================

SPIN_COST = config.SPIN_COST

SPIN_REWARDS = [
    dict(item)
    for item in config.SPIN_REWARDS
]


# ==========================================
# بارگذاری تنظیمات ذخیره شده
# ==========================================

def load_spin_settings():

    global SPIN_COST
    global SPIN_REWARDS

    # ======================================
    # هزینه چرخونه
    # ======================================

    saved_cost = get_int_setting(
        "spin_cost",
        config.SPIN_COST
    )

    if saved_cost > 0:

        SPIN_COST = saved_cost

    else:

        SPIN_COST = config.SPIN_COST

    # ======================================
    # جوایز چرخونه
    # ======================================

    saved_rewards = get_setting(
        "spin_rewards",
        None
    )

    if saved_rewards:

        try:

            rewards = json.loads(
                saved_rewards
            )

            if validate_reward_list(
                rewards
            ):

                SPIN_REWARDS = [
                    dict(item)
                    for item in rewards
                ]

        except (
            TypeError,
            ValueError,
            json.JSONDecodeError
        ):

            SPIN_REWARDS = [
                dict(item)
                for item in config.SPIN_REWARDS
            ]


# ==========================================
# اعتبارسنجی جوایز چرخونه
# ==========================================

def validate_spin_rewards():

    total = sum(
        float(item["chance"])
        for item in SPIN_REWARDS
    )

    return abs(
        total - 100
    ) < 0.000001


# ==========================================
# دریافت تنظیمات چرخونه
# ==========================================

def get_spin_settings():

    return {
        "cost": SPIN_COST,
        "rewards": [
            dict(item)
            for item in SPIN_REWARDS
        ]
    }


# ==========================================
# دریافت هزینه فعلی چرخونه
# ==========================================

def get_spin_cost():

    return SPIN_COST


# ==========================================
# دریافت جوایز فعلی چرخونه
# ==========================================

def get_spin_rewards():

    return [
        dict(item)
        for item in SPIN_REWARDS
    ]


# ==========================================
# بررسی تنظیمات جایزه
# ==========================================

def validate_reward_list(
    rewards
):

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

    # ======================================
    # ذخیره در دیتابیس
    # ======================================

    saved = set_setting(
        "spin_cost",
        new_cost
    )

    if not saved:

        return False

    # ======================================
    # تغییر مقدار Runtime
    # ======================================

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

    # ======================================
    # ذخیره JSON
    # ======================================

    try:

        rewards_json = json.dumps(
            rewards,
            ensure_ascii=False
        )

    except (
        TypeError,
        ValueError
    ):

        return False

    saved = set_setting(
        "spin_rewards",
        rewards_json
    )

    if not saved:

        return False

    # ======================================
    # تغییر مقدار Runtime
    # ======================================

    SPIN_REWARDS = [
        dict(item)
        for item in rewards
    ]

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

    # ======================================
    # ساخت نسخه جدید
    # ======================================

    new_rewards = [
        dict(item)
        for item in SPIN_REWARDS
    ]

    item = new_rewards[index]

    # ======================================
    # تغییر نام
    # ======================================

    if name is not None:

        name = str(
            name
        ).strip()

        if not name:

            return False

        item["name"] = name

    # ======================================
    # تغییر مقدار جایزه
    # ======================================

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

    # ======================================
    # تغییر احتمال
    # ======================================

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

    # ======================================
    # بررسی نهایی
    # ======================================

    if not validate_reward_list(
        new_rewards
    ):

        return False

    # ======================================
    # ذخیره
    # ======================================

    return set_spin_rewards(
        new_rewards
    )


# ==========================================
# بازگرداندن تنظیمات به حالت پیش‌فرض
# ==========================================

def reset_spin_settings():

    global SPIN_COST
    global SPIN_REWARDS

    default_cost = config.SPIN_COST

    default_rewards = [
        dict(item)
        for item in config.SPIN_REWARDS
    ]

    if not validate_reward_list(
        default_rewards
    ):

        return False

    if not set_setting(
        "spin_cost",
        default_cost
    ):

        return False

    try:

        rewards_json = json.dumps(
            default_rewards,
            ensure_ascii=False
        )

    except (
        TypeError,
        ValueError
    ):

        return False

    if not set_setting(
        "spin_rewards",
        rewards_json
    ):

        return False

    SPIN_COST = default_cost

    SPIN_REWARDS = [
        dict(item)
        for item in default_rewards
    ]

    return True


# ==========================================
# چرخاندن چرخونه
# ==========================================

def spin_wheel(
    user_id
):

    # ======================================
    # بررسی تنظیمات
    # ======================================

    if not validate_spin_rewards():

        return {
            "success": False,
            "message": (
                "تنظیمات احتمال‌های چرخونه "
                "اشتباهه."
            )
        }

    # ======================================
    # بررسی موجودی
    # ======================================

    balance = get_balance(
        user_id
    )

    if balance is None:

        return {
            "success": False,
            "message": (
                "❌ اطلاعات کیف پول "
                "پیدا نشد."
            )
        }

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

    # ======================================
    # دریافت هزینه
    # ======================================

    removed = remove_tokens(
        user_id,
        SPIN_COST,
        "🎡 هزینه چرخونه"
    )

    if not removed:

        return {
            "success": False,
            "message": (
                "❌ انجام چرخونه "
                "ممکن نشد."
            )
        }

    # ======================================
    # انتخاب جایزه
    # ======================================

    rewards = [
        dict(item)
        for item in SPIN_REWARDS
    ]

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

    # ======================================
    # پرداخت جایزه
    # ======================================

    if reward > 0:

        added = add_tokens(
            user_id,
            reward,
            f"🎡 جایزه چرخونه: {reward} ژتون"
        )

        if not added:

            # ==================================
            # برگشت هزینه در صورت خطا
            # ==================================

            add_tokens(
                user_id,
                SPIN_COST,
                "↩️ برگشت هزینه چرخونه"
            )

            return {
                "success": False,
                "message": (
                    "❌ پرداخت جایزه "
                    "انجام نشد."
                )
            }

    # ======================================
    # نتیجه
    # ======================================

    return {
        "success": True,
        "name": result["name"],
        "reward": reward,
        "cost": SPIN_COST
    }


# ==========================================
# بارگذاری تنظیمات هنگام import
# ==========================================

load_spin_settings()
