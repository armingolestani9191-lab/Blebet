# ==========================================
# BaleBet - Admin Panel
# ==========================================

import json
import threading
from concurrent.futures import ThreadPoolExecutor

import api
import config
import wallet
import referral

from api import (
    send_message,
    edit_message_text,
    answer_callback_query
)

from database import (
    get_connection,
    get_setting,
    get_int_setting,
    get_bool_setting,
    set_setting,
    get_user_count,
    get_banned_user_count,
    get_active_user_count,
    get_total_tokens,
    get_referral_count,
    get_user_admin_info,
    find_user,
    ban_user,
    unban_user,
    get_user_tokens,
    change_user_tokens
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
# تنظیمات عمومی
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


def set_token_value(value):

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
# State
# ==========================================

def set_state(
    admin_user_id,
    state,
    **data
):

    try:

        admin_user_id = int(
            admin_user_id
        )

    except (
        TypeError,
        ValueError
    ):

        return False

    admin_states[
        admin_user_id
    ] = {
        "state": state,
        **data
    }

    return True


def get_state(
    admin_user_id
):

    try:

        admin_user_id = int(
            admin_user_id
        )

    except (
        TypeError,
        ValueError
    ):

        return None

    return admin_states.get(
        admin_user_id
    )


def clear_state(
    admin_user_id
):

    try:

        admin_user_id = int(
            admin_user_id
        )

    except (
        TypeError,
        ValueError
    ):

        return

    admin_states.pop(
        admin_user_id,
        None
    )


def is_cancel(text):

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
# توابع جوین اجباری
# ==========================================

def get_force_join_channels():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            channel
        FROM force_join_channels
        ORDER BY id ASC
    """)

    rows = cursor.fetchall()

    connection.close()

    return [
        {
            "id": row[0],
            "channel": row[1]
        }
        for row in rows
    ]


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

    if channel.startswith(
        "https://t.me/"
    ):

        channel = "@" + channel[
            len("https://t.me/"):
        ]

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

    except Exception:

        connection.rollback()

        return False

    finally:

        connection.close()


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

    changed = (
        cursor.rowcount > 0
    )

    if changed:

        connection.commit()

    else:

        connection.rollback()

    connection.close()

    return changed


def is_force_join_enabled():

    return get_bool_setting(
        "force_join_enabled",
        False
    )


def set_force_join_enabled(
    enabled
):

    return set_setting(
        "force_join_enabled",
        "1" if enabled else "0"
    )


# ==========================================
# بررسی عضویت اجباری
# ==========================================

def check_force_join(
    user_id
):

    if is_admin(
        user_id
    ):

        return True

    if not is_force_join_enabled():

        return True

    channels = get_force_join_channels()

    if not channels:

        return True

    for item in channels:

        channel = item.get(
            "channel"
        )

        if not channel:

            continue

        try:

            result = api.api_request(
                "getChatMember",
                {
                    "chat_id": channel,
                    "user_id": int(user_id)
                }
            )

        except Exception:

            return False

        if not isinstance(
            result,
            dict
        ):

            return False

        if not result.get(
            "ok",
            False
        ):

            return False

        member = result.get(
            "result"
        )

        if not isinstance(
            member,
            dict
        ):

            return False

        status = member.get(
            "status"
        )

        if status in (
            "creator",
            "administrator",
            "member"
        ):

            continue

        if status == "restricted":

            if member.get(
                "is_member",
                False
            ):

                continue

        return False

    return True


# ==========================================
# متن جوین اجباری
# ==========================================

def force_join_user_text():

    channels = get_force_join_channels()

    text = (
        "📢 <b>عضویت در کانال‌ها</b>\n\n"
        "برای استفاده از ربات، ابتدا باید "
        "در کانال‌های زیر عضو بشی:\n\n"
    )

    if not channels:

        text += (
            "📭 در حال حاضر کانالی "
            "برای عضویت تنظیم نشده."
        )

        return text

    for index, item in enumerate(
        channels,
        start=1
    ):

        channel = item.get(
            "channel",
            ""
        )

        text += (
            f"{index}. "
            f"<code>{channel}</code>\n"
        )

    text += (
        "\nبعد از عضویت روی دکمه "
        "«✅ بررسی عضویت» بزن."
    )

    return text


def force_join_user_keyboard():

    channels = get_force_join_channels()

    buttons = []

    for item in channels:

        channel = str(
            item.get(
                "channel",
                ""
            )
        ).strip()

        if not channel:

            continue

        clean = channel.lstrip(
            "@"
        )

        buttons.append([
            {
                "text": (
                    f"📢 عضویت "
                    f"{channel}"
                ),
                "url": (
                    "https://t.me/" +
                    clean
                )
            }
        ])

    buttons.append([
        {
            "text": "✅ بررسی عضویت",
            "callback_data": "check_join"
        }
    ])

    return json.dumps({
        "inline_keyboard": buttons
    })


# ==========================================
# پنل اصلی
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
                    "text": "🪙 تنظیم ژتون",
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
# متن پنل
# ==========================================

def admin_panel_text():

    stats = {
        "users": get_user_count(),
        "banned_users": get_banned_user_count(),
        "active_users": get_active_user_count(),
        "tokens": get_total_tokens(),
        "referrals": get_referral_count()
    }

    force_status = (
        "🟢 روشن"
        if is_force_join_enabled()
        else
        "🔴 خاموش"
    )

    return (
        "👑 <b>پنل مدیریت BaleBet</b>\n\n"
        "📊 <b>وضعیت ربات</b>\n"
        f"👥 کاربران: "
        f"<b>{stats['users']:,}</b>\n"
        f"🟢 فعال: "
        f"<b>{stats['active_users']:,}</b>\n"
        f"🚫 بن‌شده: "
        f"<b>{stats['banned_users']:,}</b>\n"
        f"🪙 مجموع ژتون‌ها: "
        f"<b>{stats['tokens']:,}</b>\n"
        f"👥 دعوت‌ها: "
        f"<b>{stats['referrals']:,}</b>\n\n"
        f"📢 جوین اجباری: "
        f"<b>{force_status}</b>\n\n"
        "👇 یک بخش را انتخاب کن:"
    )


def admin_stats_text():

    return (
        "📊 <b>آمار ربات</b>\n\n"
        f"👥 کل کاربران:\n"
        f"<b>{get_user_count():,}</b>\n\n"
        f"🟢 کاربران فعال:\n"
        f"<b>{get_active_user_count():,}</b>\n\n"
        f"🚫 کاربران بن‌شده:\n"
        f"<b>{get_banned_user_count():,}</b>\n\n"
        f"🪙 مجموع ژتون‌ها:\n"
        f"<b>{get_total_tokens():,}</b>\n\n"
        f"👥 دعوت‌های موفق:\n"
        f"<b>{get_referral_count():,}</b>"
    )


# ==========================================
# مدیریت کاربران
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


def admin_users_text():

    return (
        "👤 <b>مدیریت کاربران</b>\n\n"
        "🔍 کاربر را با یکی از موارد زیر پیدا کن:\n\n"
        "🆔 آیدی عددی\n"
        "<code>595450272</code>\n\n"
        "👤 یوزرنیم\n"
        "<code>@username</code>"
    )


def user_info_text(
    user
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

        username = "ندارد"

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
        f"<code>{username}</code>\n\n"
        f"📝 نام:\n"
        f"<b>{user.get('first_name') or 'ندارد'}</b>\n\n"
        f"🪙 موجودی:\n"
        f"<b>{int(user.get('tokens', 0)):,}</b> ژتون\n\n"
        f"📌 وضعیت:\n"
        f"<b>{status}</b>\n\n"
        f"📅 ثبت‌نام:\n"
        f"<code>{user.get('created_at') or 'نامشخص'}</code>"
    )


def admin_user_keyboard(
    user
):

    user_id = int(
        user["user_id"]
    )

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
# بن‌شده‌ها
# ==========================================

def get_banned_users():

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
        WHERE banned = 1
        ORDER BY user_id DESC
        LIMIT 30
    """)

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


def banned_users_text():

    users = get_banned_users()

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
            f"🪙 {int(user.get('tokens', 0)):,}\n\n"
        )

    return text


# ==========================================
# جوین اجباری - پنل
# ==========================================

def force_join_keyboard():

    channels = get_force_join_channels()

    buttons = []

    for item in channels:

        channel_id = item.get(
            "id"
        )

        channel = item.get(
            "channel"
        )

        buttons.append([
            {
                "text": (
                    f"❌ حذف {channel}"
                ),
                "callback_data": (
                    f"admin_force_remove_{channel_id}"
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
                "text": (
                    f"🔘 وضعیت: {status}"
                ),
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
                "callback_data": "admin_panel"
            }
        ]

    ])

    return json.dumps({
        "inline_keyboard": buttons
    })


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

    if not channels:

        text += (
            "📭 هنوز کانالی اضافه نشده."
        )

        return text

    text += (
        "📋 <b>کانال‌های فعلی:</b>\n\n"
    )

    for index, item in enumerate(
        channels,
        start=1
    ):

        text += (
            f"{index}. "
            f"<code>{item['channel']}</code>\n"
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
                    "text": "📝 ارسال متنی",
                    "callback_data": (
                        "admin_broadcast_text"
                    )
                }
            ],

            [
                {
                    "text": "↪️ ارسال Forward",
                    "callback_data": (
                        "admin_broadcast_forward"
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


def broadcast_text():

    return (
        "📣 <b>همگانی</b>\n\n"
        "از یکی از گزینه‌های زیر استفاده کن:"
    )


def get_broadcast_users():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT user_id
        FROM users
        WHERE user_id IS NOT NULL
        AND banned = 0
        ORDER BY user_id ASC
    """)

    rows = cursor.fetchall()

    connection.close()

    return [
        row[0]
        for row in rows
    ]


def broadcast_report(
    total,
    sent,
    failed
):

    return (
        "📊 <b>گزارش همگانی</b>\n\n"
        f"👥 کل: <b>{total:,}</b>\n"
        f"✅ ارسال‌شده: <b>{sent:,}</b>\n"
        f"❌ ناموفق: <b>{failed:,}</b>"
    )


def send_text_to_user(
    user_id,
    text
):

    try:

        result = send_message(
            user_id,
            text
        )

        return bool(
            result
        )

    except Exception:

        return False


def broadcast_text_message(
    text,
    users
):

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

    workers = max(
        1,
        min(
            workers,
            50
        )
    )

    def send_one(
        user_id
    ):

        return send_text_to_user(
            user_id,
            text
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


def forward_message_to_user(
    source_chat_id,
    message_id,
    target_user_id
):

    try:

        result = api.api_request(
            "forwardMessage",
            {
                "chat_id": target_user_id,
                "from_chat_id": source_chat_id,
                "message_id": message_id
            }
        )

        return bool(
            result
            and result.get(
                "ok",
                False
            )
        )

    except Exception:

        return False


def broadcast_forward_message(
    source_chat_id,
    message_id,
    users
):

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

    workers = max(
        1,
        min(
            workers,
            50
        )
    )

    def send_one(
        user_id
    ):

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
# شروع همگانی متنی
# ==========================================

def start_text_broadcast(
    chat_id,
    text
):

    if not text:

        send_message(
            chat_id,
            "❌ متن خالیه."
        )

        return

    if not admin_broadcast_lock.acquire(
        blocking=False
    ):

        send_message(
            chat_id,
            "⏳ یک همگانی در حال انجامه."
        )

        return

    try:

        users = get_broadcast_users()

        total = len(
            users
        )

        if total == 0:

            send_message(
                chat_id,
                "📭 کاربری برای ارسال وجود نداره."
            )

            return

        send_message(
            chat_id,
            (
                "⚡ <b>ارسال شروع شد.</b>\n\n"
                f"👥 کاربران: <b>{total:,}</b>"
            )
        )

        sent, failed = broadcast_text_message(
            text,
            users
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
# شروع Forward
# ==========================================

def start_forward_broadcast(
    chat_id,
    source_chat_id,
    message_id
):

    if not source_chat_id or not message_id:

        send_message(
            chat_id,
            "❌ اطلاعات Forward کامل نیست."
        )

        return

    if not admin_broadcast_lock.acquire(
        blocking=False
    ):

        send_message(
            chat_id,
            "⏳ یک همگانی در حال انجامه."
        )

        return

    try:

        users = get_broadcast_users()

        total = len(
            users
        )

        if total == 0:

            send_message(
                chat_id,
                "📭 کاربری برای ارسال وجود نداره."
            )

            return

        send_message(
            chat_id,
            (
                "⚡ <b>Forward شروع شد.</b>\n\n"
                f"👥 کاربران: <b>{total:,}</b>"
            )
        )

        sent, failed = broadcast_forward_message(
            source_chat_id,
            message_id,
            users
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
# پردازش پیام‌های ادمین
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

    admin_user_id = user.get(
        "id"
    )

    chat_id = chat.get(
        "id"
    )

    if not admin_user_id or not chat_id:

        return False

    if not is_admin(
        admin_user_id
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
            admin_user_id
        )

        send_message(
            chat_id,
            admin_panel_text(),
            admin_keyboard()
        )

        return True

    state_data = get_state(
        admin_user_id
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
            admin_user_id
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

        target = find_user(
            text
        )

        clear_state(
            admin_user_id
        )

        if not target:

            send_message(
                chat_id,
                "❌ کاربر پیدا نشد.",
                admin_users_keyboard()
            )

            return True

        send_message(
            chat_id,
            user_info_text(
                target
            ),
            admin_user_keyboard(
                target
            )
        )

        return True

    # ======================================
    # افزایش ژتون
    # ======================================

    if state == "user_add_tokens":

        target_id = state_data.get(
            "target_user_id"
        )

        try:

            amount = int(
                str(text).strip()
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
                admin_user_id
            )

            send_message(
                chat_id,
                "❌ کاربر پیدا نشد.",
                admin_users_keyboard()
            )

            return True

        success = wallet.admin_add_tokens(
            target_id,
            amount
        )

        clear_state(
            admin_user_id
        )

        target = get_user_admin_info(
            target_id
        )

        if success and target:

            send_message(
                chat_id,
                (
                    "✅ <b>ژتون‌ها اضافه شدند.</b>\n\n"
                    f"🆔 کاربر: "
                    f"<code>{target_id}</code>\n"
                    f"➕ مقدار: "
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
                "❌ افزایش ژتون انجام نشد.",
                admin_users_keyboard()
            )

        return True

    # ======================================
    # کاهش ژتون
    # ======================================

    if state == "user_remove_tokens":

        target_id = state_data.get(
            "target_user_id"
        )

        try:

            amount = int(
                str(text).strip()
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
                admin_user_id
            )

            send_message(
                chat_id,
                "❌ کاربر پیدا نشد.",
                admin_users_keyboard()
            )

            return True

        current_tokens = int(
            target.get(
                "tokens",
                0
            )
        )

        if amount > current_tokens:

            send_message(
                chat_id,
                (
                    "❌ موجودی کاربر کافی نیست.\n\n"
                    f"🪙 موجودی فعلی: "
                    f"<b>{current_tokens:,}</b>"
                )
            )

            return True

        success = wallet.admin_remove_tokens(
            target_id,
            amount
        )

        clear_state(
            admin_user_id
        )

        target = get_user_admin_info(
            target_id
        )

        if success and target:

            send_message(
                chat_id,
                (
                    "✅ <b>ژتون‌ها کم شدند.</b>\n\n"
                    f"🆔 کاربر: "
                    f"<code>{target_id}</code>\n"
                    f"➖ مقدار: "
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
                "❌ کاهش ژتون انجام نشد.",
                admin_users_keyboard()
            )

        return True

    # ======================================
    # مقدار ژتون
    # ======================================

    if state == "token_value":

        if set_token_value(
            text
        ):

            clear_state(
                admin_user_id
            )

            send_message(
                chat_id,
                (
                    "✅ تنظیم ذخیره شد.\n\n"
                    f"🪙 مقدار: "
                    f"<b>{get_token_value():,}</b>"
                ),
                admin_keyboard()
            )

        else:

            send_message(
                chat_id,
                "❌ عدد مثبت وارد کن."
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
                admin_user_id
            )

            send_message(
                chat_id,
                (
                    "✅ جایزه دعوت‌کننده تغییر کرد.\n\n"
                    f"🎁 مقدار جدید: "
                    f"<b>{referral.get_referrer_reward():,}</b> ژتون"
                ),
                admin_keyboard()
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
                admin_user_id
            )

            send_message(
                chat_id,
                (
                    "✅ جایزه دعوت‌شونده تغییر کرد.\n\n"
                    f"🎁 مقدار جدید: "
                    f"<b>{referral.get_referred_reward():,}</b> ژتون"
                ),
                admin_keyboard()
            )

        else:

            send_message(
                chat_id,
                "❌ مقدار صحیح نیست."
            )

        return True

    # ======================================
    # افزودن کانال
    # ======================================

    if state == "force_join_add":

        if add_force_join_channel(
            text
        ):

            clear_state(
                admin_user_id
            )

            send_message(
                chat_id,
                (
                    "✅ کانال اضافه شد.\n\n" +
                    force_join_text()
                ),
                force_join_keyboard()
            )

        else:

            send_message(
                chat_id,
                (
                    "❌ اضافه کردن کانال انجام نشد.\n"
                    "ممکنه کانال قبلاً وجود داشته باشه."
                )
            )

        return True

    # ======================================
    # همگانی متنی
    # ======================================

    if state == "broadcast_text":

        clear_state(
            admin_user_id
        )

        start_text_broadcast(
            chat_id,
            text
        )

        return True

    # ======================================
    # همگانی Forward
    # ======================================

    if state == "broadcast_forward":

        source_chat_id = message.get(
            "chat",
            {}
        ).get(
            "id"
        )

        message_id = message.get(
            "message_id"
        )

        clear_state(
            admin_user_id
        )

        start_forward_broadcast(
            chat_id,
            source_chat_id,
            message_id
        )

        return True

    return True


# ==========================================
# پردازش Callback پنل
# ==========================================

def handle_callback(
    callback
):

    data = callback.get(
        "data"
    )

    if not data:

        return False

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

    admin_user_id = user.get(
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

    if not admin_user_id or not chat_id:

        return True

    if not is_admin(
        admin_user_id
    ):

        return True

    # ======================================
    # پنل اصلی
    # ======================================

    if data == "admin_panel":

        clear_state(
            admin_user_id
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
            admin_user_id
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
            admin_user_id
        )

        edit_message_text(
            chat_id,
            message_id,
            admin_users_text(),
            admin_users_keyboard()
        )

        return True

    # ======================================
    # جستجو
    # ======================================

    if data == "admin_user_search":

        set_state(
            admin_user_id,
            "user_search"
        )

        edit_message_text(
            chat_id,
            message_id,
            (
                "🔍 <b>جستجوی کاربر</b>\n\n"
                "آیدی عددی یا یوزرنیم رو بفرست.\n\n"
                "مثال:\n"
                "<code>595450272</code>\n"
                "<code>@username</code>\n\n"
                "برای لغو: <b>لغو</b>"
            ),
            admin_back_keyboard()
        )

        return True

    # ======================================
    # کاربران بن‌شده
    # ======================================

    if data == "admin_banned_users":

        clear_state(
            admin_user_id
        )

        edit_message_text(
            chat_id,
            message_id,
            banned_users_text(),
            admin_back_keyboard()
        )

        return True

    # ======================================
    # تنظیم ژتون
    # ======================================

    if data == "admin_token":

        set_state(
            admin_user_id,
            "token_value"
        )

        edit_message_text(
            chat_id,
            message_id,
            (
                "🪙 <b>تنظیم ژتون</b>\n\n"
                f"مقدار فعلی:\n"
                f"<b>{get_token_value():,}</b>\n\n"
                "مقدار جدید رو بفرست.\n\n"
                "برای لغو: <b>لغو</b>"
            ),
            admin_back_keyboard()
        )

        return True

    # ======================================
    # جایزه دعوت‌کننده
    # ======================================

    if data == "admin_referrer":

        set_state(
            admin_user_id,
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
            admin_user_id,
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
    # جوین اجباری
    # ======================================

    if data == "admin_force_join":

        clear_state(
            admin_user_id
        )

        edit_message_text(
            chat_id,
            message_id,
            force_join_text(),
            force_join_keyboard()
        )

        return True

    # ======================================
    # روشن / خاموش
    # ======================================

    if data == "admin_force_toggle":

        current = is_force_join_enabled()

        if set_force_join_enabled(
            not current
        ):

            status = (
                "روشن"
                if not current
                else
                "خاموش"
            )

            edit_message_text(
                chat_id,
                message_id,
                (
                    f"✅ جوین اجباری "
                    f"<b>{status}</b> شد.\n\n" +
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
            admin_user_id,
            "force_join_add"
        )

        edit_message_text(
            chat_id,
            message_id,
            (
                "➕ <b>افزودن کانال</b>\n\n"
                "یوزرنیم کانال رو بفرست.\n\n"
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

            channel_id = int(
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

        if remove_force_join_channel_by_id(
            channel_id
        ):

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
            admin_user_id
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
            admin_user_id,
            "broadcast_text"
        )

        edit_message_text(
            chat_id,
            message_id,
            (
                "📣 <b>همگانی متنی</b>\n\n"
                "متنی که می‌خوای برای همه "
                "کاربران ارسال بشه رو بفرست.\n\n"
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
            admin_user_id,
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

        # ==================================
        # بن
        # ==================================

        if action == "ban":

            if target_id == int(
                config.ADMIN_ID
            ):

                edit_message_text(
                    chat_id,
                    message_id,
                    "❌ نمی‌تونی خود ادمین رو بن کنی.",
                    admin_user_keyboard(
                        get_user_admin_info(
                            target_id
                        )
                    )
                )

                return True

            success = ban_user(
                target_id
            )

            target = get_user_admin_info(
                target_id
            )

            if success and target:

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

            else:

                edit_message_text(
                    chat_id,
                    message_id,
                    "❌ بن کردن انجام نشد.",
                    admin_users_keyboard()
                )

            return True

        # ==================================
        # آن‌بن
        # ==================================

        if action == "unban":

            success = unban_user(
                target_id
            )

            target = get_user_admin_info(
                target_id
            )

            if success and target:

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

            else:

                edit_message_text(
                    chat_id,
                    message_id,
                    "❌ آن‌بن کردن انجام نشد.",
                    admin_users_keyboard()
                )

            return True

        # ==================================
        # بروزرسانی
        # ==================================

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

        # ==================================
        # افزایش ژتون
        # ==================================

        if action == "add":

            target = get_user_admin_info(
                target_id
            )

            if not target:

                edit_message_text(
                    chat_id,
                    message_id,
                    "❌ کاربر پیدا نشد.",
                    admin_users_keyboard()
                )

                return True

            # نکته مهم:
            # target_id با نام user_id ذخیره نمی‌شود.
            # چون user_id قبلاً پارامتر ادمین set_state است.

            set_state(
                admin_user_id,
                "user_add_tokens",
                target_user_id=target_id
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

        # ==================================
        # کاهش ژتون
        # ==================================

        if action == "remove":

            target = get_user_admin_info(
                target_id
            )

            if not target:

                edit_message_text(
                    chat_id,
                    message_id,
                    "❌ کاربر پیدا نشد.",
                    admin_users_keyboard()
                )

                return True

            # اصلاح اصلی باگ:
            # قبلاً user_id=target_id
            # باعث تکراری شدن آرگومان user_id می‌شد.

            set_state(
                admin_user_id,
                "user_remove_tokens",
                target_user_id=target_id
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
