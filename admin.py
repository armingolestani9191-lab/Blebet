# ==========================================
# BaleBet - Admin Panel
# ==========================================

import json
import threading
from concurrent.futures import ThreadPoolExecutor

import api
import config
import games
import referral
import wallet

from api import (
    send_message,
    edit_message_text,
    answer_callback_query
)

from database import (
    get_setting,
    get_int_setting,
    get_bool_setting,
    set_setting,
    get_admin_stats,
    get_recent_users,
    get_banned_users,
    find_user,
    get_user_admin_info,
    ban_user,
    unban_user,
    get_force_join_channels,
    add_force_join_channel,
    remove_force_join_channel_by_id,
    is_force_join_enabled,
    set_force_join_enabled
)

# ==========================================
# وضعیت‌های موقت پنل
# ==========================================

admin_states = {}

admin_broadcast_lock = threading.Lock()


# ==========================================
# بررسی ادمین
# ==========================================

def is_admin(user_id):

    try:
        return int(user_id) == int(
            config.ADMIN_ID
        )

    except (
        TypeError,
        ValueError
    ):
        return False


# ==========================================
# تنظیمات عمومی پنل
# ==========================================

def get_token_value():

    return get_int_setting(
        "token_value",
        getattr(
            config,
            "TOKEN_VALUE",
            0
        )
    )


def set_token_value(
    value
):

    try:
        value = int(value)

    except (
        TypeError,
        ValueError
    ):
        return False

    if value <= 0:
        return False

    return set_setting(
        "token_value",
        value
    )


# ==========================================
# کیبورد پنل اصلی
# ==========================================

def admin_keyboard():

    return json.dumps({
        "inline_keyboard": [

            [
                {
                    "text": "📊 آمار",
                    "callback_data": "admin_stats"
                },
                {
                    "text": "👤 مدیریت کاربران",
                    "callback_data": "admin_users"
                }
            ],

            [
                {
                    "text": "🪙 قیمت ژتون",
                    "callback_data": "admin_token"
                }
            ],

            [
                {
                    "text": "🎁 جایزه دعوت‌کننده",
                    "callback_data": "admin_referrer"
                },
                {
                    "text": "🎁 جایزه دعوت‌شونده",
                    "callback_data": "admin_referred"
                }
            ],

            [
                {
                    "text": "🎡 تنظیمات چرخونه",
                    "callback_data": "admin_spin"
                }
            ],

            [
                {
                    "text": "📢 جوین اجباری",
                    "callback_data": "admin_force_join"
                }
            ],

            [
                {
                    "text": "📣 همگانی",
                    "callback_data": "admin_broadcast"
                }
            ],

            [
                {
                    "text": "‹ بازگشت",
                    "callback_data": "home"
                }
            ]

        ]
    })


# ==========================================
# کیبورد بازگشت به پنل
# ==========================================

def admin_back_keyboard():

    return json.dumps({
        "inline_keyboard": [

            [
                {
                    "text": "‹ بازگشت به پنل",
                    "callback_data": "admin_panel"
                }
            ]

        ]
    })


# ==========================================
# متن پنل اصلی
# ==========================================

def admin_panel_text():

    stats = get_admin_stats()

    force_join = is_force_join_enabled()

    force_status = (
        "🟢 روشن"
        if force_join
        else
        "🔴 خاموش"
    )

    return (
        "👑 <b>پنل مدیریت BaleBet</b>\n\n"

        "📊 <b>وضعیت ربات</b>\n"
        f"👥 کاربران: <b>{stats['users']:,}</b>\n"
        f"🟢 فعال: <b>{stats['active_users']:,}</b>\n"
        f"🚫 بن‌شده: <b>{stats['banned_users']:,}</b>\n"
        f"🪙 مجموع ژتون‌ها: "
        f"<b>{stats['tokens']:,}</b>\n"
        f"👥 دعوت‌ها: "
        f"<b>{stats['referrals']:,}</b>\n\n"

        f"📢 جوین اجباری: <b>{force_status}</b>\n\n"

        "👇 یک بخش را انتخاب کن:"
    )


# ==========================================
# متن آمار
# ==========================================

def admin_stats_text():

    stats = get_admin_stats()

    return (
        "📊 <b>آمار ربات</b>\n\n"

        f"👥 کل کاربران:\n"
        f"<b>{stats['users']:,}</b>\n\n"

        f"🟢 کاربران فعال:\n"
        f"<b>{stats['active_users']:,}</b>\n\n"

        f"🚫 کاربران بن‌شده:\n"
        f"<b>{stats['banned_users']:,}</b>\n\n"

        f"🪙 مجموع ژتون کاربران:\n"
        f"<b>{stats['tokens']:,}</b>\n\n"

        f"👥 دعوت‌های موفق:\n"
        f"<b>{stats['referrals']:,}</b>\n\n"

        f"💳 تعداد تراکنش‌ها:\n"
        f"<b>{stats['transactions']:,}</b>"
    )


# ==========================================
# کیبورد مدیریت کاربران
# ==========================================

def admin_users_keyboard():

    return json.dumps({
        "inline_keyboard": [

            [
                {
                    "text": "🔍 جستجوی کاربر",
                    "callback_data": "admin_user_search"
                }
            ],

            [
                {
                    "text": "👥 آخرین کاربران",
                    "callback_data": "admin_recent_users"
                }
            ],

            [
                {
                    "text": "🚫 کاربران بن‌شده",
                    "callback_data": "admin_banned_users"
                }
            ],

            [
                {
                    "text": "‹ بازگشت",
                    "callback_data": "admin_panel"
                }
            ]

        ]
    })


# ==========================================
# متن مدیریت کاربران
# ==========================================

def admin_users_text():

    return (
        "👤 <b>مدیریت کاربران</b>\n\n"

        "🔍 می‌تونی کاربر رو با یکی از این‌ها پیدا کنی:\n\n"

        "🆔 آیدی عددی\n"
        "مثال:\n"
        "<code>595450272</code>\n\n"

        "👤 یوزرنیم\n"
        "مثال:\n"
        "<code>@username</code>"
    )


# ==========================================
# نمایش اطلاعات کاربر
# ==========================================

def user_info_text(user):

    username = user.get(
        "username"
    )

    if username:
        username_text = (
            f"@{str(username).lstrip('@')}"
        )
    else:
        username_text = "ندارد"

    status = (
        "🚫 بن‌شده"
        if user.get("banned")
        else
        "🟢 فعال"
    )

    return (
        "👤 <b>اطلاعات کاربر</b>\n\n"

        f"🆔 آیدی:\n"
        f"<code>{user['user_id']}</code>\n\n"

        f"👤 یوزرنیم:\n"
        f"<code>{username_text}</code>\n\n"

        f"📝 نام:\n"
        f"<b>{user.get('first_name') or 'ندارد'}</b>\n\n"

        f"🪙 موجودی:\n"
        f"<b>{user.get('tokens', 0):,}</b> ژتون\n\n"

        f"📌 وضعیت:\n"
        f"<b>{status}</b>\n\n"

        f"📅 ثبت‌نام:\n"
        f"<code>{user.get('created_at') or 'نامشخص'}</code>"
    )


# ==========================================
# کیبورد مدیریت یک کاربر
# ==========================================

def admin_user_keyboard(
    user
):

    user_id = user["user_id"]

    if user.get("banned"):

        ban_button = {
            "text": "✅ آن‌بن",
            "callback_data": (
                f"admin_user_unban_{user_id}"
            )
        }

    else:

        ban_button = {
            "text": "🚫 بن",
            "callback_data": (
                f"admin_user_ban_{user_id}"
            )
        }

    return json.dumps({
        "inline_keyboard": [

            [
                ban_button
            ],

            [
                {
                    "text": "➕ افزایش ژتون",
                    "callback_data": (
                        f"admin_user_add_{user_id}"
                    )
                },
                {
                    "text": "➖ کاهش ژتون",
                    "callback_data": (
                        f"admin_user_remove_{user_id}"
                    )
                }
            ],

            [
                {
                    "text": "🔄 بروزرسانی",
                    "callback_data": (
                        f"admin_user_refresh_{user_id}"
                    )
                }
            ],

            [
                {
                    "text": "‹ بازگشت",
                    "callback_data": "admin_users"
                }
            ]

        ]
    })


# ==========================================
# آخرین کاربران
# ==========================================

def recent_users_text():

    users = get_recent_users(
        15
    )

    if not users:

        return (
            "👥 <b>آخرین کاربران</b>\n\n"
            "هیچ کاربری پیدا نشد."
        )

    text = (
        "👥 <b>آخرین کاربران</b>\n\n"
    )

    for index, user in enumerate(
        users,
        start=1
    ):

        username = user.get(
            "username"
        )

        if username:
            username = (
                "@" +
                str(username).lstrip("@")
            )

        else:
            username = "بدون یوزرنیم"

        status = (
            "🚫"
            if user.get("banned")
            else
            "🟢"
        )

        text += (
            f"{index}. {status} "
            f"<b>{user.get('first_name') or 'بدون نام'}</b>\n"
            f"🆔 <code>{user['user_id']}</code>\n"
            f"👤 {username}\n"
            f"🪙 {user.get('tokens', 0):,}\n\n"
        )

    return text


# ==========================================
# کاربران بن‌شده
# ==========================================

def banned_users_text():

    users = get_banned_users(
        15
    )

    if not users:

        return (
            "🚫 <b>کاربران بن‌شده</b>\n\n"
            "هیچ کاربر بن‌شده‌ای وجود ندارد."
        )

    text = (
        "🚫 <b>کاربران بن‌شده</b>\n\n"
    )

    for index, user in enumerate(
        users,
        start=1
    ):

        username = user.get(
            "username"
        )

        if username:
            username = (
                "@" +
                str(username).lstrip("@")
            )

        else:
            username = "بدون یوزرنیم"

        text += (
            f"{index}. "
            f"<b>{user.get('first_name') or 'بدون نام'}</b>\n"
            f"🆔 <code>{user['user_id']}</code>\n"
            f"👤 {username}\n"
            f"🪙 {user.get('tokens', 0):,}\n\n"
        )

    return text


# ==========================================
# کیبورد تنظیمات دعوت
# ==========================================

def admin_referral_keyboard():

    return json.dumps({
        "inline_keyboard": [

            [
                {
                    "text": "🎁 جایزه دعوت‌کننده",
                    "callback_data": (
                        "admin_referrer"
                    )
                }
            ],

            [
                {
                    "text": "🎁 جایزه دعوت‌شونده",
                    "callback_data": (
                        "admin_referred"
                    )
                }
            ],

            [
                {
                    "text": "‹ بازگشت",
                    "callback_data": "admin_panel"
                }
            ]

        ]
    })


# ==========================================
# متن تنظیمات دعوت
# ==========================================

def referral_settings_text():

    return (
        "🎁 <b>تنظیمات دعوت</b>\n\n"

        f"👤 پاداش دعوت‌کننده:\n"
        f"<b>{referral.get_referrer_reward():,}</b> ژتون\n\n"

        f"🎁 پاداش دعوت‌شونده:\n"
        f"<b>{referral.get_referred_reward():,}</b> ژتون\n\n"

        "👇 موردی که می‌خوای تغییر بدی رو انتخاب کن:"
    )


# ==========================================
# کیبورد چرخونه
# ==========================================

def admin_spin_keyboard():

    return json.dumps({
        "inline_keyboard": [

            [
                {
                    "text": "💰 تغییر هزینه چرخش",
                    "callback_data": (
                        "admin_spin_cost"
                    )
                }
            ],

            [
                {
                    "text": "🎁 مدیریت جوایز",
                    "callback_data": (
                        "admin_spin_rewards"
                    )
                }
            ],

            [
                {
                    "text": "🔄 بازنشانی پیش‌فرض",
                    "callback_data": (
                        "admin_spin_reset"
                    )
                }
            ],

            [
                {
                    "text": "‹ بازگشت",
                    "callback_data": "admin_panel"
                }
            ]

        ]
    })


# ==========================================
# متن تنظیمات چرخونه
# ==========================================

def spin_settings_text():

    settings = games.get_spin_settings()

    text = (
        "🎡 <b>تنظیمات چرخونه</b>\n\n"

        f"💰 هزینه هر چرخش:\n"
        f"<b>{settings['cost']:,}</b> ژتون\n\n"

        "🎁 <b>جوایز فعلی:</b>\n\n"
    )

    for index, item in enumerate(
        settings["rewards"],
        start=1
    ):

        text += (
            f"{index}. {item['name']}\n"
            f"🪙 جایزه: "
            f"<b>{int(item['reward']):,}</b>\n"
            f"🎯 احتمال: "
            f"<b>{item['chance']}%</b>\n\n"
        )

    return text


# ==========================================
# کیبورد جوایز چرخونه
# ==========================================

def spin_rewards_keyboard():

    rewards = games.get_spin_rewards()

    buttons = []

    for index, item in enumerate(
        rewards
    ):

        buttons.append([
            {
                "text": (
                    f"✏️ {index + 1}. "
                    f"{item['name']}"
                ),
                "callback_data": (
                    f"admin_reward_{index}"
                )
            }
        ])

    buttons.append([
        {
            "text": "‹ بازگشت",
            "callback_data": "admin_spin"
        }
    ])

    return json.dumps({
        "inline_keyboard": buttons
    })


# ==========================================
# متن مدیریت جوایز
# ==========================================

def spin_rewards_text():

    rewards = games.get_spin_rewards()

    text = (
        "🎁 <b>مدیریت جوایز چرخونه</b>\n\n"
        "روی جایزه موردنظر بزن:\n\n"
    )

    for index, item in enumerate(
        rewards,
        start=1
    ):

        text += (
            f"{index}. {item['name']} → "
            f"<b>{int(item['reward']):,}</b> ژتون\n"
            f"🎯 احتمال: "
            f"<b>{item['chance']}%</b>\n\n"
        )

    text += (
        "⚠️ مجموع احتمال‌ها باید دقیقاً "
        "<b>100%</b> باشد."
    )

    return text


# ==========================================
# کیبورد و متن ویرایش جایزه
# ==========================================

def reward_edit_keyboard(
    index
):

    return json.dumps({
        "inline_keyboard": [

            [
                {
                    "text": "📝 تغییر نام",
                    "callback_data": (
                        f"admin_reward_name_{index}"
                    )
                }
            ],

            [
                {
                    "text": "🪙 تغییر مقدار",
                    "callback_data": (
                        f"admin_reward_value_{index}"
                    )
                }
            ],

            [
                {
                    "text": "🎯 تغییر احتمال",
                    "callback_data": (
                        f"admin_reward_chance_{index}"
                    )
                }
            ],

            [
                {
                    "text": "‹ بازگشت",
                    "callback_data": (
                        "admin_spin_rewards"
                    )
                }
            ]

        ]
    })


# ==========================================
# جوین اجباری
# ==========================================

def force_join_keyboard():

    channels = get_force_join_channels()

    buttons = []

    for index, channel in enumerate(
        channels
    ):

        buttons.append([
            {
                "text": f"❌ حذف {channel}",
                "callback_data": (
                    f"admin_force_remove_{index}"
                )
            }
        ])

    status = (
        "🟢 روشن"
        if is_force_join_enabled()
        else
        "🔴 خاموش"
    )

    buttons.extend([

        [
            {
                "text": f"🔘 وضعیت: {status}",
                "callback_data": (
                    "admin_force_toggle"
                )
            }
        ],

        [
            {
                "text": "➕ افزودن کانال",
                "callback_data": (
                    "admin_force_add"
                )
            }
        ],

        [
            {
                "text": "‹ بازگشت",
                "callback_data": (
                    "admin_panel"
                )
            }
        ]

    ])

    return json.dumps({
        "inline_keyboard": buttons
    })


# ==========================================
# متن جوین اجباری
# ==========================================

def force_join_text():

    channels = get_force_join_channels()

    status = (
        "🟢 روشن"
        if is_force_join_enabled()
        else
        "🔴 خاموش"
    )

    text = (
        "📢 <b>جوین اجباری</b>\n\n"
        f"وضعیت: <b>{status}</b>\n\n"
    )

    if channels:

        text += (
            "📋 <b>کانال‌های فعلی:</b>\n\n"
        )

        for index, channel in enumerate(
            channels,
            start=1
        ):

            text += (
                f"{index}. "
                f"<code>{channel}</code>\n"
            )

    else:

        text += (
            "📭 هنوز کانالی اضافه نشده.\n"
        )

    return text


# ==========================================
# همگانی
# ==========================================

def broadcast_keyboard():

    return json.dumps({
        "inline_keyboard": [

            [
                {
                    "text": "📣 همگانی متنی",
                    "callback_data": (
                        "admin_broadcast_text"
                    )
                }
            ],

            [
                {
                    "text": "↪️ Forward",
                    "callback_data": (
                        "admin_broadcast_forward"
                    )
                }
            ],

            [
                {
                    "text": "‹ بازگشت",
                    "callback_data": (
                        "admin_panel"
                    )
                }
            ]

        ]
    })


# ==========================================
# متن همگانی
# ==========================================

def broadcast_text():

    return (
        "📣 <b>ارسال همگانی</b>\n\n"

        "از این بخش می‌تونی یک پیام رو برای "
        "تمام کاربران ارسال کنی.\n\n"

        "📣 <b>همگانی متنی</b>\n"
        "متن پیام رو ازت می‌گیره.\n\n"

        "↪️ <b>Forward</b>\n"
        "پیام رو Forward می‌کنی و همون پیام "
        "برای کاربران ارسال می‌شه.\n\n"

        "⚡ ارسال‌ها به صورت سریع و همزمان انجام می‌شن.\n\n"

        "📊 بعد از پایان، گزارش کامل ارسال می‌شه."
    )


# ==========================================
# پیام وضعیت Broadcast
# ==========================================

def broadcast_report(
    total,
    sent,
    failed
):

    return (
        "📊 <b>گزارش همگانی</b>\n\n"

        f"👥 تعداد کل:\n"
        f"<b>{total:,}</b>\n\n"

        f"✅ موفق:\n"
        f"<b>{sent:,}</b>\n\n"

        f"❌ ناموفق:\n"
        f"<b>{failed:,}</b>\n\n"

        f"📈 درصد موفقیت:\n"
        f"<b>{(
            (sent / total * 100)
            if total
            else 0
        ):.1f}%</b>"
    )


# ==========================================
# استخراج پیام برای Forward
# ==========================================

def get_message_id(
    message
):

    if not isinstance(
        message,
        dict
    ):
        return None

    return message.get(
        "message_id"
    )


# ==========================================
# ارسال همگانی متنی
# ==========================================

def broadcast_text_message(
    text,
    users
):

    if not users:
        return (
            0,
            0
        )

    sent = 0
    failed = 0

    try:

        workers = int(
            getattr(
                config,
                "BROADCAST_CONCURRENCY",
                20
            )
        )

    except (
        TypeError,
        ValueError
    ):

        workers = 20

    if workers <= 0:
        workers = 1

    if workers > 50:
        workers = 50

    delay = getattr(
        config,
        "BROADCAST_DELAY",
        0
    )

    try:
        delay = float(delay)

    except (
        TypeError,
        ValueError
    ):
        delay = 0

    def send_one(
        user
    ):

        user_id = user.get(
            "user_id"
        )

        if not user_id:
            return False

        result = send_message(
            user_id,
            text
        )

        if not result:
            return False

        if isinstance(
            result,
            dict
        ):
            return bool(
                result.get(
                    "ok",
                    False
                )
            )

        return True

    with ThreadPoolExecutor(
        max_workers=workers
    ) as executor:

        results = executor.map(
            send_one,
            users
        )

        for result in results:

            if result:
                sent += 1

            else:
                failed += 1

            if delay > 0:

                # فقط برای کنترل فشار API
                threading.Event().wait(
                    delay
                )

    return (
        sent,
        failed
    )


# ==========================================
# ارسال Forward
# ==========================================

def forward_message_to_user(
    source_chat_id,
    message_id,
    user_id
):

    result = api.api_request(
        "forwardMessage",
        {
            "chat_id": user_id,
            "from_chat_id": source_chat_id,
            "message_id": message_id
        }
    )

    if not result:
        return False

    return bool(
        result.get(
            "ok",
            False
        )
    )


# ==========================================
# ارسال Forward همگانی
# ==========================================

def broadcast_forward_message(
    source_chat_id,
    message_id,
    users
):

    if not users:
        return (
            0,
            0
        )

    sent = 0
    failed = 0

    try:

        workers = int(
            getattr(
                config,
                "BROADCAST_CONCURRENCY",
                20
            )
        )

    except (
        TypeError,
        ValueError
    ):

        workers = 20

    if workers <= 0:
        workers = 1

    if workers > 50:
        workers = 50

    def send_one(
        user
    ):

        user_id = user.get(
            "user_id"
        )

        if not user_id:
            return False

        return forward_message_to_user(
            source_chat_id,
            message_id,
            user_id
        )

    with ThreadPoolExecutor(
        max_workers=workers
    ) as executor:

        results = executor.map(
            send_one,
            users
        )

        for result in results:

            if result:
                sent += 1

            else:
                failed += 1

    return (
        sent,
        failed
    )


# ==========================================
# شروع Broadcast متنی
# ==========================================

def start_text_broadcast(
    chat_id,
    text
):

    if not text:
        send_message(
            chat_id,
            "❌ متن پیام خالیه."
        )
        return

    if not admin_broadcast_lock.acquire(
        blocking=False
    ):

        send_message(
            chat_id,
            "⏳ یک ارسال همگانی در حال انجامه.\n"
            "لطفاً صبر کن تا تمام بشه."
        )

        return

    try:

        from database import get_all_users

        users = get_all_users()

        total = len(
            users
        )

        if total == 0:

            send_message(
                chat_id,
                "📭 هیچ کاربری برای ارسال وجود نداره."
            )

            return

        send_message(
            chat_id,
            (
                "⚡ <b>ارسال سریع شروع شد.</b>\n\n"
                f"👥 تعداد کاربران: <b>{total:,}</b>"
            )
        )

        sent, failed = (
            broadcast_text_message(
                text,
                users
            )
        )

        send_message(
            chat_id,
            broadcast_report(
                total,
                sent,
                failed
            ),
            admin_back_keyboard()
        )

    finally:

        admin_broadcast_lock.release()


# ==========================================
# شروع Broadcast Forward
# ==========================================

def start_forward_broadcast(
    chat_id,
    source_chat_id,
    message_id
):

    if not source_chat_id or not message_id:

        send_message(
            chat_id,
            "❌ اطلاعات پیام برای Forward کامل نیست."
        )

        return

    if not admin_broadcast_lock.acquire(
        blocking=False
    ):

        send_message(
            chat_id,
            "⏳ یک ارسال همگانی در حال انجامه.\n"
            "لطفاً صبر کن."
        )

        return

    try:

        from database import get_all_users

        users = get_all_users()

        total = len(
            users
        )

        if total == 0:

            send_message(
                chat_id,
                "📭 هیچ کاربری برای ارسال وجود نداره."
            )

            return

        send_message(
            chat_id,
            (
                "⚡ <b>ارسال Forward شروع شد.</b>\n\n"
                f"👥 تعداد کاربران: <b>{total:,}</b>"
            )
        )

        sent, failed = (
            broadcast_forward_message(
                source_chat_id,
                message_id,
                users
            )
        )

        send_message(
            chat_id,
            broadcast_report(
                total,
                sent,
                failed
            ),
            admin_back_keyboard()
        )

    finally:

        admin_broadcast_lock.release()


# ==========================================
# ذخیره State
# ==========================================

def set_state(
    user_id,
    state,
    **data
):

    admin_states[
        int(user_id)
    ] = {
        "state": state,
        **data
    }


# ==========================================
# دریافت State
# ==========================================

def get_state(
    user_id
):

    return admin_states.get(
        int(user_id)
    )


# ==========================================
# حذف State
# ==========================================

def clear_state(
    user_id
):

    admin_states.pop(
        int(user_id),
        None
    )


# ==========================================
# بررسی لغو
# ==========================================

def is_cancel(
    text
):

    if text is None:
        return False

    return str(
        text
    ).strip().lower() in (
        "لغو",
        "/cancel",
        "cancel"
    )


# ==========================================
# پردازش پیام‌های پنل
# ==========================================

def handle_message(
    message
):

    chat = message.get(
        "chat",
        {}
    )

    user = message.get(
        "from",
        {}
    )

    user_id = user.get(
        "id"
    )

    chat_id = chat.get(
        "id"
    )

    if not user_id or not chat_id:
        return False

    if not is_admin(
        user_id
    ):

        return False

    text = message.get(
        "text",
        ""
    )

    # ======================================
    # /admin
    # ======================================

    if text == "/admin":

        clear_state(
            user_id
        )

        send_message(
            chat_id,
            admin_panel_text(),
            admin_keyboard()
        )

        return True

    # ======================================
    # اگر State نداریم
    # ======================================

    state_data = get_state(
        user_id
    )

    if not state_data:

        return False

    state = state_data.get(
        "state"
    )

    # ======================================
    # لغو
    # ======================================

    if is_cancel(
        text
    ):

        clear_state(
            user_id
        )

        send_message(
            chat_id,
            "❌ عملیات لغو شد.",
            admin_keyboard()
        )

        return True

    # ======================================
    # جستجوی کاربر
    # ======================================

    if state == "user_search":

        user = find_user(
            text
        )

        clear_state(
            user_id
        )

        if not user:

            send_message(
                chat_id,
                (
                    "❌ کاربر پیدا نشد.\n\n"
                    "با ID عددی یا Username دوباره امتحان کن."
                ),
                admin_users_keyboard()
            )

            return True

        send_message(
            chat_id,
            user_info_text(
                user
            ),
            admin_user_keyboard(
                user
            )
        )

        return True

    # ======================================
    # افزایش موجودی
    # ======================================

    if state == "user_add_tokens":

        target_id = state_data.get(
            "user_id"
        )

        try:
            amount = int(
                text.strip()
            )

        except (
            TypeError,
            ValueError
        ):

            send_message(
                chat_id,
                "❌ فقط عدد مثبت وارد کن."
            )

            return True

        if amount <= 0:

            send_message(
                chat_id,
                "❌ مقدار باید بیشتر از صفر باشه."
            )

            return True

        success = wallet.admin_add_tokens(
            target_id,
            amount
        )

        clear_state(
            user_id
        )

        target = get_user_admin_info(
            target_id
        )

        if success and target:

            send_message(
                chat_id,
                (
                    "✅ موجودی با موفقیت افزایش پیدا کرد.\n\n"
                    f"🪙 مقدار افزایش: "
                    f"<b>{amount:,}</b>\n"
                    f"🪙 موجودی جدید: "
                    f"<b>{target['tokens']:,}</b>"
                ),
                admin_user_keyboard(
                    target
                )
            )

        else:

            send_message(
                chat_id,
                "❌ افزایش موجودی انجام نشد.",
                admin_users_keyboard()
            )

        return True

    # ======================================
    # کاهش موجودی
    # ======================================

    if state == "user_remove_tokens":

        target_id = state_data.get(
            "user_id"
        )

        try:
            amount = int(
                text.strip()
            )

        except (
            TypeError,
            ValueError
        ):

            send_message(
                chat_id,
                "❌ فقط عدد مثبت وارد کن."
            )

            return True

        if amount <= 0:

            send_message(
                chat_id,
                "❌ مقدار باید بیشتر از صفر باشه."
            )

            return True

        target = get_user_admin_info(
            target_id
        )

        if not target:

            clear_state(
                user_id
            )

            send_message(
                chat_id,
                "❌ کاربر پیدا نشد.",
                admin_users_keyboard()
            )

            return True

        if amount > int(
            target.get(
                "tokens",
                0
            )
        ):

            send_message(
                chat_id,
                (
                    "❌ موجودی کاربر کافی نیست.\n\n"
                    f"🪙 موجودی فعلی: "
                    f"<b>{target['tokens']:,}</b>"
                )
            )

            return True

        success = wallet.admin_remove_tokens(
            target_id,
            amount
        )

        clear_state(
            user_id
        )

        target = get_user_admin_info(
            target_id
        )

        if success and target:

            send_message(
                chat_id,
                (
                    "✅ موجودی با موفقیت کاهش پیدا کرد.\n\n"
                    f"🪙 مقدار کاهش: "
                    f"<b>{amount:,}</b>\n"
                    f"🪙 موجودی جدید: "
                    f"<b>{target['tokens']:,}</b>"
                ),
                admin_user_keyboard(
                    target
                )
            )

        else:

            send_message(
                chat_id,
                "❌ کاهش موجودی انجام نشد.",
                admin_users_keyboard()
            )

        return True

    # ======================================
    # قیمت ژتون
    # ======================================

    if state == "token_value":

        if set_token_value(
            text
        ):

            clear_state(
                user_id
            )

            send_message(
                chat_id,
                (
                    "✅ قیمت هر ژتون تغییر کرد.\n\n"
                    f"🪙 قیمت جدید: "
                    f"<b>{get_token_value():,}</b> تومان"
                ),
                admin_keyboard()
            )

        else:

            send_message(
                chat_id,
                "❌ مقدار صحیح نیست.\n"
                "یک عدد مثبت وارد کن."
            )

        return True

    # ======================================
    # جایزه دعوت‌کننده
    # ======================================

    if state == "referrer_reward":

        if referral.set_referrer_reward(
            text
        ):

            clear_state(
                user_id
            )

            send_message(
                chat_id,
                (
                    "✅ پاداش دعوت‌کننده تغییر کرد.\n\n"
                    f"🎁 مقدار جدید: "
                    f"<b>{referral.get_referrer_reward():,}</b> ژتون"
                ),
                admin_referral_keyboard()
            )

        else:

            send_message(
                chat_id,
                "❌ مقدار صحیح نیست."
            )

        return True

    # ======================================
    # جایزه دعوت‌شونده
    # ======================================

    if state == "referred_reward":

        if referral.set_referred_reward(
            text
        ):

            clear_state(
                user_id
            )

            send_message(
                chat_id,
                (
                    "✅ پاداش دعوت‌شونده تغییر کرد.\n\n"
                    f"🎁 مقدار جدید: "
                    f"<b>{referral.get_referred_reward():,}</b> ژتون"
                ),
                admin_referral_keyboard()
            )

        else:

            send_message(
                chat_id,
                "❌ مقدار صحیح نیست."
            )

        return True

    # ======================================
    # هزینه چرخونه
    # ======================================

    if state == "spin_cost":

        if games.set_spin_cost(
            text
        ):

            clear_state(
                user_id
            )

            send_message(
                chat_id,
                (
                    "✅ هزینه چرخونه تغییر کرد.\n\n"
                    f"💰 هزینه جدید: "
                    f"<b>{games.get_spin_cost():,}</b> ژتون"
                ),
                admin_spin_keyboard()
            )

        else:

            send_message(
                chat_id,
                "❌ مقدار صحیح نیست."
            )

        return True

    # ======================================
    # تغییر نام جایزه
    # ======================================

    if state == "reward_name":

        index = state_data.get(
            "index"
        )

        if games.update_spin_reward(
            index,
            name=text.strip()
        ):

            clear_state(
                user_id
            )

            send_message(
                chat_id,
                "✅ نام جایزه تغییر کرد.",
                spin_rewards_keyboard()
            )

        else:

            send_message(
                chat_id,
                "❌ تغییر نام انجام نشد."
            )

        return True

    # ======================================
    # تغییر مقدار جایزه
    # ======================================

    if state == "reward_value":

        index = state_data.get(
            "index"
        )

        try:
            value = int(
                text.strip()
            )

        except (
            TypeError,
            ValueError
        ):

            send_message(
                chat_id,
                "❌ فقط عدد وارد کن."
            )

            return True

        if value < 0:

            send_message(
                chat_id,
                "❌ مقدار نمی‌تونه منفی باشه."
            )

            return True

        if games.update_spin_reward(
            index,
            reward=value
        ):

            clear_state(
                user_id
            )

            send_message(
                chat_id,
                "✅ مقدار جایزه تغییر کرد.",
                spin_rewards_keyboard()
            )

        else:

            send_message(
                chat_id,
                (
                    "❌ تغییر انجام نشد.\n"
                    "احتمالاً مجموع احتمال‌ها مشکل دارد."
                )
            )

        return True

    # ======================================
    # تغییر احتمال جایزه
    # ======================================

    if state == "reward_chance":

        index = state_data.get(
            "index"
        )

        try:
            chance = float(
                text.strip()
            )

        except (
            TypeError,
            ValueError
        ):

            send_message(
                chat_id,
                "❌ فقط عدد وارد کن."
            )

            return True

        if chance < 0:

            send_message(
                chat_id,
                "❌ احتمال نمی‌تونه منفی باشه."
            )

            return True

        if games.update_spin_reward(
            index,
            chance=chance
        ):

            clear_state(
                user_id
            )

            send_message(
                chat_id,
                "✅ احتمال جایزه تغییر کرد.",
                spin_rewards_keyboard()
            )

        else:

            send_message(
                chat_id,
                (
                    "❌ تغییر انجام نشد.\n\n"
                    "⚠️ مجموع احتمال تمام جایزه‌ها "
                    "باید دقیقاً 100٪ باشد."
                )
            )

        return True

    # ======================================
    # افزودن کانال جوین اجباری
    # ======================================

    if state == "force_join_add":

        channel = text.strip()

        if not channel.startswith("@"):

            channel = (
                "@" + channel
            )

        if add_force_join_channel(
            channel
        ):

            clear_state(
                user_id
            )

            send_message(
                chat_id,
                (
                    "✅ کانال اضافه شد.\n\n"
                    f"📢 {channel}"
                ),
                force_join_keyboard()
            )

        else:

            send_message(
                chat_id,
                (
                    "❌ کانال اضافه نشد.\n"
                    "ممکنه قبلاً وجود داشته باشه."
                )
            )

        return True

    # ======================================
    # Broadcast متنی
    # ======================================

    if state == "broadcast_text":

        clear_state(
            user_id
        )

        start_text_broadcast(
            chat_id,
            text
        )

        return True

    # ======================================
    # Broadcast Forward
    # ======================================

    if state == "broadcast_forward":

        message_id = get_message_id(
            message
        )

        clear_state(
            user_id
        )

        if not message_id:

            send_message(
                chat_id,
                "❌ پیام قابل Forward پیدا نشد."
            )

            return True

        start_forward_broadcast(
            chat_id,
            chat_id,
            message_id
        )

        return True

    return True


# ==========================================
# پردازش Callbackهای پنل
# ==========================================

def handle_callback(
    callback
):

    data = callback.get(
        "data"
    )

    if not data:
        return False

    # فقط Callbackهای خود پنل
    if not data.startswith(
        "admin_"
    ):

        return False

    callback_id = callback.get(
        "id"
    )

    if callback_id:

        answer_callback_query(
            callback_id
        )

    user = callback.get(
        "from",
        {}
    )

    user_id = user.get(
        "id"
    )

    message = callback.get(
        "message",
        {}
    )

    chat = message.get(
        "chat",
        {}
    )

    chat_id = chat.get(
        "id"
    )

    message_id = message.get(
        "message_id"
    )

    if not user_id or not chat_id:

        return True

    if not is_admin(
        user_id
    ):

        return True

    # ======================================
    # پنل اصلی
    # ======================================

    if data == "admin_panel":

        clear_state(
            user_id
        )

        edit_message_text(
            chat_id,
            message_id,
            admin_panel_text(),
            admin_keyboard()
        )

        return True

    # ======================================
    # آمار
    # ======================================

    if data == "admin_stats":

        clear_state(
            user_id
        )

        edit_message_text(
            chat_id,
            message_id,
            admin_stats_text(),
            admin_back_keyboard()
        )

        return True

    # ======================================
    # مدیریت کاربران
    # ======================================

    if data == "admin_users":

        clear_state(
            user_id
        )

        edit_message_text(
            chat_id,
            message_id,
            admin_users_text(),
            admin_users_keyboard()
        )

        return True

    # ======================================
    # جستجوی کاربر
    # ======================================

    if data == "admin_user_search":

        set_state(
            user_id,
            "user_search"
        )

        edit_message_text(
            chat_id,
            message_id,
            (
                "🔍 <b>جستجوی کاربر</b>\n\n"
                "ID عددی یا Username کاربر رو بفرست.\n\n"
                "مثال:\n"
                "<code>595450272</code>\n"
                "<code>@username</code>\n\n"
                "برای لغو: <b>لغو</b>"
            ),
            admin_back_keyboard()
        )

        return True

    # ======================================
    # آخرین کاربران
    # ======================================

    if data == "admin_recent_users":

        clear_state(
            user_id
        )

        edit_message_text(
            chat_id,
            message_id,
            recent_users_text(),
            admin_back_keyboard()
        )

        return True

    # ======================================
    # کاربران بن‌شده
    # ======================================

    if data == "admin_banned_users":

        clear_state(
            user_id
        )

        edit_message_text(
            chat_id,
            message_id,
            banned_users_text(),
            admin_back_keyboard()
        )

        return True

    # ======================================
    # قیمت ژتون
    # ======================================

    if data == "admin_token":

        set_state(
            user_id,
            "token_value"
        )

        edit_message_text(
            chat_id,
            message_id,
            (
                "🪙 <b>قیمت ژتون</b>\n\n"
                f"قیمت فعلی هر ژتون:\n"
                f"<b>{get_token_value():,}</b> تومان\n\n"
                "قیمت جدید رو به صورت عدد بفرست.\n\n"
                "برای لغو: <b>لغو</b>"
            ),
            admin_back_keyboard()
        )

        return True

    # ======================================
    # تنظیمات دعوت
    # ======================================

    if data == "admin_referral":

        clear_state(
            user_id
        )

        edit_message_text(
            chat_id,
            message_id,
            referral_settings_text(),
            admin_referral_keyboard()
        )

        return True

    # ======================================
    # جایزه دعوت‌کننده
    # ======================================

    if data == "admin_referrer":

        set_state(
            user_id,
            "referrer_reward"
        )

        edit_message_text(
            chat_id,
            message_id,
            (
                "🎁 <b>جایزه دعوت‌کننده</b>\n\n"
                f"مقدار فعلی:\n"
                f"<b>{referral.get_referrer_reward():,}</b> ژتون\n\n"
                "مقدار جدید رو بفرست.\n\n"
                "برای لغو: <b>لغو</b>"
            ),
            admin_back_keyboard()
        )

        return True

    # ======================================
    # جایزه دعوت‌شونده
    # ======================================

    if data == "admin_referred":

        set_state(
            user_id,
            "referred_reward"
        )

        edit_message_text(
            chat_id,
            message_id,
            (
                "🎁 <b>جایزه دعوت‌شونده</b>\n\n"
                f"مقدار فعلی:\n"
                f"<b>{referral.get_referred_reward():,}</b> ژتون\n\n"
                "مقدار جدید رو بفرست.\n\n"
                "برای لغو: <b>لغو</b>"
            ),
            admin_back_keyboard()
        )

        return True

    # ======================================
    # تنظیمات چرخونه
    # ======================================

    if data == "admin_spin":

        clear_state(
            user_id
        )

        edit_message_text(
            chat_id,
            message_id,
            spin_settings_text(),
            admin_spin_keyboard()
        )

        return True

    # ======================================
    # هزینه چرخونه
    # ======================================

    if data == "admin_spin_cost":

        set_state(
            user_id,
            "spin_cost"
        )

        edit_message_text(
            chat_id,
            message_id,
            (
                "💰 <b>هزینه چرخونه</b>\n\n"
                f"هزینه فعلی:\n"
                f"<b>{games.get_spin_cost():,}</b> ژتون\n\n"
                "هزینه جدید رو بفرست.\n\n"
                "برای لغو: <b>لغو</b>"
            ),
            admin_back_keyboard()
        )

        return True

    # ======================================
    # مدیریت جوایز چرخونه
    # ======================================

    if data == "admin_spin_rewards":

        clear_state(
            user_id
        )

        edit_message_text(
            chat_id,
            message_id,
            spin_rewards_text(),
            spin_rewards_keyboard()
        )

        return True

    # ======================================
    # ویرایش جایزه
    # ======================================

    if data.startswith(
        "admin_reward_"
    ):

        parts = data.split(
            "_"
        )

        # admin_reward_INDEX
        if len(parts) == 3:

            try:
                index = int(
                    parts[2]
                )

            except ValueError:

                return True

            rewards = games.get_spin_rewards()

            if (
                index < 0
                or index >= len(rewards)
            ):

                return True

            item = rewards[index]

            edit_message_text(
                chat_id,
                message_id,
                (
                    "🎁 <b>ویرایش جایزه</b>\n\n"
                    f"{item['name']}\n\n"
                    f"🪙 مقدار: "
                    f"<b>{item['reward']}</b>\n"
                    f"🎯 احتمال: "
                    f"<b>{item['chance']}%</b>"
                ),
                reward_edit_keyboard(
                    index
                )
            )

            return True

        # admin_reward_name_INDEX
        if len(parts) == 4 and parts[2] == "name":

            try:
                index = int(
                    parts[3]
                )

            except ValueError:

                return True

            set_state(
                user_id,
                "reward_name",
                index=index
            )

            edit_message_text(
                chat_id,
                message_id,
                (
                    "📝 <b>تغییر نام جایزه</b>\n\n"
                    "نام جدید جایزه رو بفرست.\n\n"
                    "برای لغو: <b>لغو</b>"
                ),
                admin_back_keyboard()
            )

            return True

        # admin_reward_value_INDEX
        if len(parts) == 4 and parts[2] == "value":

            try:
                index = int(
                    parts[3]
                )

            except ValueError:

                return True

            set_state(
                user_id,
                "reward_value",
                index=index
            )

            edit_message_text(
                chat_id,
                message_id,
                (
                    "🪙 <b>تغییر مقدار جایزه</b>\n\n"
                    "مقدار جدید رو به عدد بفرست.\n\n"
                    "برای لغو: <b>لغو</b>"
                ),
                admin_back_keyboard()
            )

            return True

        # admin_reward_chance_INDEX
        if len(parts) == 4 and parts[2] == "chance":

            try:
                index = int(
                    parts[3]
                )

            except ValueError:

                return True

            set_state(
                user_id,
                "reward_chance",
                index=index
            )

            edit_message_text(
                chat_id,
                message_id,
                (
                    "🎯 <b>تغییر احتمال جایزه</b>\n\n"
                    "احتمال جدید رو وارد کن.\n"
                    "مثلاً: <code>12.5</code>\n\n"
                    "⚠️ مجموع احتمال‌ها باید 100٪ بشه.\n\n"
                    "برای لغو: <b>لغو</b>"
                ),
                admin_back_keyboard()
            )

            return True

    # ======================================
    # بازنشانی چرخونه
    # ======================================

    if data == "admin_spin_reset":

        clear_state(
            user_id
        )

        if games.reset_spin_settings():

            edit_message_text(
                chat_id,
                message_id,
                (
                    "✅ تنظیمات چرخونه به حالت پیش‌فرض برگشت."
                    "\n\n" +
                    spin_settings_text()
                ),
                admin_spin_keyboard()
            )

        else:

            edit_message_text(
                chat_id,
                message_id,
                "❌ بازنشانی تنظیمات انجام نشد.",
                admin_spin_keyboard()
            )

        return True

    # ======================================
    # جوین اجباری
    # ======================================

    if data == "admin_force_join":

        clear_state(
            user_id
        )

        edit_message_text(
            chat_id,
            message_id,
            force_join_text(),
            force_join_keyboard()
        )

        return True

    # ======================================
    # روشن / خاموش جوین اجباری
    # ======================================

    if data == "admin_force_toggle":

        current = is_force_join_enabled()

        if set_force_join_enabled(
            not current
        ):

            new_status = (
                "روشن"
                if not current
                else
                "خاموش"
            )

            edit_message_text(
                chat_id,
                message_id,
                (
                    f"✅ جوین اجباری <b>{new_status}</b> شد.\n\n"
                    +
                    force_join_text()
                ),
                force_join_keyboard()
            )

        else:

            edit_message_text(
                chat_id,
                message_id,
                "❌ تغییر وضعیت انجام نشد.",
                force_join_keyboard()
            )

        return True

    # ======================================
    # افزودن کانال
    # ======================================

    if data == "admin_force_add":

        set_state(
            user_id,
            "force_join_add"
        )

        edit_message_text(
            chat_id,
            message_id,
            (
                "➕ <b>افزودن کانال</b>\n\n"
                "Username کانال رو بفرست.\n\n"
                "مثال:\n"
                "<code>@mychannel</code>\n\n"
                "برای لغو: <b>لغو</b>"
            ),
            admin_back_keyboard()
        )

        return True

    # ======================================
    # حذف کانال
    # ======================================

    if data.startswith(
        "admin_force_remove_"
    ):

        try:

            index = int(
                data.rsplit(
                    "_",
                    1
                )[1]
            )

        except (
            TypeError,
            ValueError
        ):

            return True

        channels = get_force_join_channels()

        if (
            index < 0
            or index >= len(channels)
        ):

            return True

        # دیتابیس حذف بر اساس ID دارد،
        # ولی لیست عمومی فقط channel برمی‌گرداند.
        # بنابراین حذف را با connection مستقیم انجام نمی‌دهیم.
        # از تابع موجود بر اساس channel استفاده می‌کنیم.

        from database import (
            remove_force_join_channel
        )

        channel = channels[index]

        removed = remove_force_join_channel(
            channel
        )

        if removed:

            edit_message_text(
                chat_id,
                message_id,
                (
                    "✅ کانال حذف شد.\n\n" +
                    force_join_text()
                ),
                force_join_keyboard()
            )

        else:

            edit_message_text(
                chat_id,
                message_id,
                "❌ حذف کانال انجام نشد.",
                force_join_keyboard()
            )

        return True

    # ======================================
    # همگانی
    # ======================================

    if data == "admin_broadcast":

        clear_state(
            user_id
        )

        edit_message_text(
            chat_id,
            message_id,
            broadcast_text(),
            broadcast_keyboard()
        )

        return True

    # ======================================
    # همگانی متنی
    # ======================================

    if data == "admin_broadcast_text":

        set_state(
            user_id,
            "broadcast_text"
        )

        edit_message_text(
            chat_id,
            message_id,
            (
                "📣 <b>همگانی متنی</b>\n\n"
                "متنی که می‌خوای برای همه کاربران "
                "ارسال بشه رو بفرست.\n\n"
                "⚡ ارسال سریع انجام می‌شه.\n\n"
                "برای لغو: <b>لغو</b>"
            ),
            admin_back_keyboard()
        )

        return True

    # ======================================
    # Forward
    # ======================================

    if data == "admin_broadcast_forward":

        set_state(
            user_id,
            "broadcast_forward"
        )

        edit_message_text(
            chat_id,
            message_id,
            (
                "↪️ <b>ارسال Forward</b>\n\n"
                "پیامی که می‌خوای برای همه "
                "ارسال بشه رو همینجا Forward کن.\n\n"
                "برای لغو: <b>لغو</b>"
            ),
            admin_back_keyboard()
        )

        return True

    # ======================================
    # مدیریت کاربر
    # ======================================

    if data.startswith(
        "admin_user_"
    ):

        parts = data.split(
            "_"
        )

        # admin_user_ACTION_ID

        if len(parts) < 4:

            return True

        action = parts[2]

        try:

            target_id = int(
                "_".join(
                    parts[3:]
                )
            )

        except (
            TypeError,
            ValueError
        ):

            return True

        # ------------------------------
        # بن
        # ------------------------------

        if action == "ban":

            if ban_user(
                target_id
            ):

                target = get_user_admin_info(
                    target_id
                )

                if target:

                    edit_message_text(
                        chat_id,
                        message_id,
                        (
                            "🚫 <b>کاربر بن شد.</b>\n\n" +
                            user_info_text(
                                target
                            )
                        ),
                        admin_user_keyboard(
                            target
                        )
                    )

            return True

        # ------------------------------
        # آن‌بن
        # ------------------------------

        if action == "unban":

            if unban_user(
                target_id
            ):

                target = get_user_admin_info(
                    target_id
                )

                if target:

                    edit_message_text(
                        chat_id,
                        message_id,
                        (
                            "✅ <b>کاربر آن‌بن شد.</b>\n\n" +
                            user_info_text(
                                target
                            )
                        ),
                        admin_user_keyboard(
                            target
                        )
                    )

            return True

        # ------------------------------
        # بروزرسانی
        # ------------------------------

        if action == "refresh":

            target = get_user_admin_info(
                target_id
            )

            if target:

                edit_message_text(
                    chat_id,
                    message_id,
                    user_info_text(
                        target
                    ),
                    admin_user_keyboard(
                        target
                    )
                )

            else:

                edit_message_text(
                    chat_id,
                    message_id,
                    "❌ کاربر پیدا نشد.",
                    admin_users_keyboard()
                )

            return True

        # ------------------------------
        # افزایش
        # ------------------------------

        if action == "add":

            set_state(
                user_id,
                "user_add_tokens",
                user_id=target_id
            )

            edit_message_text(
                chat_id,
                message_id,
                (
                    "➕ <b>افزایش ژتون</b>\n\n"
                    f"🆔 کاربر:\n"
                    f"<code>{target_id}</code>\n\n"
                    "مقدار ژتون رو بفرست.\n\n"
                    "برای لغو: <b>لغو</b>"
                ),
                admin_back_keyboard()
            )

            return True

        # ------------------------------
        # کاهش
        # ------------------------------

        if action == "remove":

            set_state(
                user_id,
                "user_remove_tokens",
                user_id=target_id
            )

            edit_message_text(
                chat_id,
                message_id,
                (
                    "➖ <b>کاهش ژتون</b>\n\n"
                    f"🆔 کاربر:\n"
                    f"<code>{target_id}</code>\n\n"
                    "مقدار ژتون رو بفرست.\n\n"
                    "برای لغو: <b>لغو</b>"
                ),
                admin_back_keyboard()
            )

            return True

    return True
