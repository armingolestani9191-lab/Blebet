# ==========================================
# BaleBet - Bot
# ==========================================

import json
import time
import threading

import api
import config
import games
import referral
import wallet

from api import (
    get_updates,
    send_message,
    edit_message_text,
    answer_callback_query
)

from users import (
    get_or_create_user,
    update_activity,
    get_active_users
)

from wallet import (
    get_balance,
    get_balance_value
)

from referral import (
    create_referral,
    get_referral_count
)

from games import (
    spin_wheel
)

from config import (
    TOKEN_VALUE,
    REFERRER_REWARD,
    REFERRED_REWARD,
    SPIN_COST,
    SPIN_REWARDS,
    ADMIN_ID
)


# ==========================================
# وضعیت‌های موقت ادمین
# ==========================================

admin_states = {}

broadcast_lock = threading.Lock()


# ==========================================
# بررسی ادمین
# ==========================================

def is_admin(user_id):

    try:
        return int(user_id) == int(ADMIN_ID)

    except Exception:
        return False


# ==========================================
# کیبورد اصلی
# ==========================================

def main_keyboard():

    return json.dumps({
        "inline_keyboard": [

            [
                {
                    "text": "🎮 بازی‌ها",
                    "callback_data": "games"
                },
                {
                    "text": "🪙 کیف پول",
                    "callback_data": "wallet"
                }
            ],

            [
                {
                    "text": "🎁 جایزه روزانه",
                    "callback_data": "daily"
                },
                {
                    "text": "👥 دعوت دوستان",
                    "callback_data": "referral"
                }
            ],

            [
                {
                    "text": "👤 حساب من",
                    "callback_data": "profile"
                },
                {
                    "text": "🏆 رتبه‌بندی",
                    "callback_data": "ranking"
                }
            ],

            [
                {
                    "text": "📜 تاریخچه",
                    "callback_data": "history"
                },
                {
                    "text": "ℹ️ راهنما",
                    "callback_data": "help"
                }
            ]

        ]
    })


# ==========================================
# کیبورد بازی‌ها
# ==========================================

def games_keyboard():

    return json.dumps({
        "inline_keyboard": [

            [
                {
                    "text": "🎡 چرخونه",
                    "callback_data": "wheel"
                }
            ],

            [
                {
                    "text": "‹ بازگشت به منو",
                    "callback_data": "home"
                }
            ]

        ]
    })


# ==========================================
# دکمه بازگشت
# ==========================================

def back_keyboard():

    return json.dumps({
        "inline_keyboard": [

            [
                {
                    "text": "‹ بازگشت به منو",
                    "callback_data": "home"
                }
            ]

        ]
    })


# ==========================================
# متن صفحه اصلی
# ==========================================

def main_text(user_id):

    tokens = get_balance(
        user_id
    )

    value = get_balance_value(
        tokens
    )

    active_users = get_active_users()

    return (
        "🎰 <b>BaleBet</b>\n\n"
        "🍀 خوش اومدی! شانس با توئه.\n\n"
        f"🟢 کاربران درحال بازی: "
        f"<b>{active_users:,}</b> نفر\n\n"
        f"🪙 موجودی ژتون: "
        f"<b>{tokens:,}</b>\n"
        f"💵 ارزش کل به تومان: "
        f"<b>{value:,}</b>\n\n"
        "👇 انتخاب کن:"
    )


# ==========================================
# ثبت فعالیت کاربر
# ==========================================

def register_user_activity(
    user_id,
    username=None,
    first_name=""
):

    get_or_create_user(
        user_id,
        username,
        first_name
    )

    update_activity(
        user_id
    )


# ==========================================
# متن دعوت دوستان
# ==========================================

def referral_text(user_id):

    count = get_referral_count(
        user_id
    )

    return (
        "👥 <b>دعوت دوستان</b>\n\n"
        "🎁 دوستات رو دعوت کن و ژتون بگیر!\n\n"
        f"👤 پاداش شما: "
        f"<b>{referral.REFERRER_REWARD}</b> ژتون\n"
        f"🎁 پاداش دوستت: "
        f"<b>{referral.REFERRED_REWARD}</b> ژتون\n\n"
        f"👥 تعداد دعوت‌های موفق: "
        f"<b>{count}</b>\n\n"
        "🔗 لینک دعوت اختصاصی شما:\n"
        "<code>لینک در تنظیمات بات قرار می‌گیرد</code>"
    )


# ==========================================
# ذخیره تنظیمات در config.py
# ==========================================

def save_config_value(name, value):

    try:

        path = "config.py"

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as file:

            content = file.read()

        lines = content.splitlines()

        replaced = False

        for index, line in enumerate(lines):

            stripped = line.strip()

            if stripped.startswith(
                f"{name} ="
            ):

                if isinstance(value, str):

                    new_value = (
                        f'{name} = "{value}"'
                    )

                else:

                    new_value = (
                        f"{name} = {repr(value)}"
                    )

                lines[index] = new_value

                replaced = True

                break

        if not replaced:

            lines.append(
                f"{name} = {repr(value)}"
            )

        with open(
            path,
            "w",
            encoding="utf-8"
        ) as file:

            file.write(
                "\n".join(lines) + "\n"
            )

        return True

    except Exception as error:

        print(
            f"Config save error: {error}"
        )

        return False


# ==========================================
# به‌روزرسانی تنظیمات در زمان اجرا
# ==========================================

def update_runtime_settings():

    global TOKEN_VALUE
    global REFERRER_REWARD
    global REFERRED_REWARD
    global SPIN_COST
    global SPIN_REWARDS

    TOKEN_VALUE = config.TOKEN_VALUE

    REFERRER_REWARD = config.REFERRER_REWARD
    REFERRED_REWARD = config.REFERRED_REWARD

    SPIN_COST = config.SPIN_COST
    SPIN_REWARDS = config.SPIN_REWARDS

    wallet.TOKEN_VALUE = config.TOKEN_VALUE

    referral.REFERRER_REWARD = (
        config.REFERRER_REWARD
    )

    referral.REFERRED_REWARD = (
        config.REFERRED_REWARD
    )

    games.SPIN_COST = config.SPIN_COST
    games.SPIN_REWARDS = config.SPIN_REWARDS


# ==========================================
# تنظیم مقدار تنظیمات
# ==========================================

def change_setting(
    name,
    value
):

    try:

        value = int(value)

        if value < 0:
            return False

        if name == "TOKEN_VALUE":

            config.TOKEN_VALUE = value

        elif name == "REFERRER_REWARD":

            config.REFERRER_REWARD = value

        elif name == "REFERRED_REWARD":

            config.REFERRED_REWARD = value

        elif name == "SPIN_COST":

            if value <= 0:
                return False

            config.SPIN_COST = value

        else:

            return False

        if not save_config_value(
            name,
            value
        ):

            return False

        update_runtime_settings()

        return True

    except Exception:

        return False


# ==========================================
# متن پنل ادمین
# ==========================================

def admin_panel_text():

    return (
        "👑 <b>پنل مدیریت BaleBet</b>\n\n"
        "از بخش‌های زیر می‌تونی تنظیمات ربات رو مدیریت کنی.\n\n"
        f"🪙 ارزش هر ژتون: "
        f"<b>{config.TOKEN_VALUE:,}</b> تومان\n"
        f"👥 پاداش دعوت‌کننده: "
        f"<b>{config.REFERRER_REWARD:,}</b> ژتون\n"
        f"🎁 پاداش دعوت‌شونده: "
        f"<b>{config.REFERRED_REWARD:,}</b> ژتون\n"
        f"🎡 هزینه چرخونه: "
        f"<b>{config.SPIN_COST:,}</b> ژتون"
    )


# ==========================================
# کیبورد پنل ادمین
# ==========================================

def admin_keyboard():

    return json.dumps({
        "inline_keyboard": [

            [
                {
                    "text": "🪙 ارزش ژتون",
                    "callback_data": "admin_token"
                },
                {
                    "text": "👥 پاداش دعوت",
                    "callback_data": "admin_ref"
                }
            ],

            [
                {
                    "text": "🎁 پاداش دعوت‌شونده",
                    "callback_data": "admin_referred"
                },
                {
                    "text": "🎡 تنظیم چرخونه",
                    "callback_data": "admin_spin"
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
                    "text": "📢 جوین اجباری",
                    "callback_data": "admin_forcejoin"
                }
            ],

            [
                {
                    "text": "📊 آمار ربات",
                    "callback_data": "admin_stats"
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
# کیبورد تنظیمات چرخونه
# ==========================================

def admin_spin_keyboard():

    return json.dumps({
        "inline_keyboard": [

            [
                {
                    "text": "💰 تغییر هزینه چرخش",
                    "callback_data": "admin_spin_cost"
                }
            ],

            [
                {
                    "text": "📋 نمایش جوایز",
                    "callback_data": "admin_spin_rewards"
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
# کیبورد جوین اجباری
# ==========================================

def admin_forcejoin_keyboard():

    channels = getattr(
        config,
        "FORCE_JOIN_CHANNELS",
        []
    )

    buttons = []

    for index, channel in enumerate(
        channels
    ):

        buttons.append([
            {
                "text": f"❌ حذف {channel}",
                "callback_data": (
                    f"force_remove_{index}"
                )
            }
        ])

    buttons.extend([

        [
            {
                "text": "➕ افزودن کانال",
                "callback_data": "force_add"
            }
        ],

        [
            {
                "text": "🔄 روشن / خاموش",
                "callback_data": "force_toggle"
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


# ==========================================
# ذخیره لیست جوین اجباری
# ==========================================

def save_force_join():

    channels = getattr(
        config,
        "FORCE_JOIN_CHANNELS",
        []
    )

    return save_config_value(
        "FORCE_JOIN_CHANNELS",
        channels
    )


# ==========================================
# بررسی عضویت کاربر
# ==========================================

def check_force_join(user_id):

    enabled = getattr(
        config,
        "FORCE_JOIN_ENABLED",
        False
    )

    if not enabled:

        return True

    channels = getattr(
        config,
        "FORCE_JOIN_CHANNELS",
        []
    )

    if not channels:

        return True

    for channel in channels:

        try:

            result = api.api_request(
                "getChatMember",
                {
                    "chat_id": channel,
                    "user_id": user_id
                }
            )

            if not result:
                return False

            if not result.get(
                "ok",
                False
            ):

                return False

            member = result.get(
                "result",
                {}
            )

            status = member.get(
                "status"
            )

            if status not in (
                "creator",
                "administrator",
                "member"
            ):

                return False

        except Exception:

            return False

    return True


# ==========================================
# پیام جوین اجباری
# ==========================================

def force_join_text():

    channels = getattr(
        config,
        "FORCE_JOIN_CHANNELS",
        []
    )

    text = (
        "🔒 <b>عضویت اجباری</b>\n\n"
        "برای استفاده از ربات باید اول "
        "در کانال‌های زیر عضو بشی:\n\n"
    )

    for channel in channels:

        text += (
            f"📢 <code>{channel}</code>\n"
        )

    text += (
        "\n✅ بعد از عضویت دوباره /start "
        "رو بزن."
    )

    return text


# ==========================================
# کیبورد جوین اجباری کاربر
# ==========================================

def force_join_keyboard():

    channels = getattr(
        config,
        "FORCE_JOIN_CHANNELS",
        []
    )

    rows = []

    for channel in channels:

        clean = str(
            channel
        ).replace(
            "@",
            ""
        )

        rows.append([
            {
                "text": f"📢 عضویت در {channel}",
                "url": f"https://ble.ir/{clean}"
            }
        ])

    rows.append([
        {
            "text": "✅ بررسی عضویت",
            "callback_data": "check_join"
        }
    ])

    return json.dumps({
        "inline_keyboard": rows
    })


# ==========================================
# آمار ادمین
# ==========================================

def get_admin_stats():

    try:

        from database import get_connection

        connection = get_connection()

        cursor = connection.cursor()

        cursor.execute(
            "SELECT COUNT(*) FROM users"
        )

        users = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COALESCE(SUM(tokens), 0) FROM users"
        )

        tokens = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM referrals"
        )

        referrals_count = cursor.fetchone()[0]

        connection.close()

        return (
            users,
            tokens,
            referrals_count
        )

    except Exception:

        return 0, 0, 0


# ==========================================
# همگانی سریع
# ==========================================

def broadcast_message(text):

    if broadcast_lock.locked():

        return 0, 0

    with broadcast_lock:

        try:

            from database import get_connection

            connection = get_connection()

            cursor = connection.cursor()

            cursor.execute(
                "SELECT user_id FROM users"
            )

            users = cursor.fetchall()

            connection.close()

        except Exception:

            return 0, 0

        success = 0
        failed = 0

        for row in users:

            user_id = row[0]

            try:

                result = send_message(
                    user_id,
                    text
                )

                if result and result.get(
                    "ok",
                    False
                ):

                    success += 1

                else:

                    failed += 1

            except Exception:

                failed += 1

            time.sleep(
                0.05
            )

        return success, failed


# ==========================================
# پردازش پیام
# ==========================================

def handle_message(message):

    chat = message.get(
        "chat",
        {}
    )

    user = message.get(
        "from",
        {}
    )

    text = message.get(
        "text",
        ""
    )

    chat_id = chat.get(
        "id"
    )

    user_id = user.get(
        "id"
    )

    if not chat_id or not user_id:

        return

    username = user.get(
        "username"
    )

    first_name = user.get(
        "first_name",
        ""
    )

    register_user_activity(
        user_id,
        username,
        first_name
    )

    # ======================================
    # ورودی‌های پنل ادمین
    # ======================================

    if is_admin(user_id):

        state = admin_states.get(
            user_id
        )

        if state:

            if text == "لغو":

                admin_states.pop(
                    user_id,
                    None
                )

                send_message(
                    chat_id,
                    "❌ عملیات لغو شد.",
                    admin_keyboard()
                )

                return

            # ------------------------------
            # تغییر ارزش ژتون
            # ------------------------------

            if state == "token_value":

                if change_setting(
                    "TOKEN_VALUE",
                    text
                ):

                    admin_states.pop(
                        user_id,
                        None
                    )

                    send_message(
                        chat_id,
                        "✅ ارزش هر ژتون با موفقیت تغییر کرد.",
                        admin_keyboard()
                    )

                else:

                    send_message(
                        chat_id,
                        "❌ مقدار وارد شده صحیح نیست.\n\n"
                        "فقط عدد مثبت وارد کن."
                    )

                return

            # ------------------------------
            # پاداش دعوت‌کننده
            # ------------------------------

            if state == "referrer_reward":

                if change_setting(
                    "REFERRER_REWARD",
                    text
                ):

                    admin_states.pop(
                        user_id,
                        None
                    )

                    send_message(
                        chat_id,
                        "✅ پاداش دعوت‌کننده تغییر کرد.",
                        admin_keyboard()
                    )

                else:

                    send_message(
                        chat_id,
                        "❌ مقدار وارد شده صحیح نیست."
                    )

                return

            # ------------------------------
            # پاداش دعوت‌شونده
            # ------------------------------

            if state == "referred_reward":

                if change_setting(
                    "REFERRED_REWARD",
                    text
                ):

                    admin_states.pop(
                        user_id,
                        None
                    )

                    send_message(
                        chat_id,
                        "✅ پاداش دعوت‌شونده تغییر کرد.",
                        admin_keyboard()
                    )

                else:

                    send_message(
                        chat_id,
                        "❌ مقدار وارد شده صحیح نیست."
                    )

                return

            # ------------------------------
            # هزینه چرخونه
            # ------------------------------

            if state == "spin_cost":

                if change_setting(
                    "SPIN_COST",
                    text
                ):

                    admin_states.pop(
                        user_id,
                        None
                    )

                    send_message(
                        chat_id,
                        "✅ هزینه چرخونه تغییر کرد.",
                        admin_spin_keyboard()
                    )

                else:

                    send_message(
                        chat_id,
                        "❌ مقدار وارد شده صحیح نیست."
                    )

                return

            # ------------------------------
            # افزودن کانال
            # ------------------------------

            if state == "force_add":

                channel = text.strip()

                if not channel:

                    send_message(
                        chat_id,
                        "❌ آیدی کانال خالیه."
                    )

                    return

                if not channel.startswith("@"):

                    channel = "@" + channel

                channels = getattr(
                    config,
                    "FORCE_JOIN_CHANNELS",
                    []
                )

                if channel not in channels:

                    channels.append(
                        channel
                    )

                config.FORCE_JOIN_CHANNELS = (
                    channels
                )

                save_force_join()

                admin_states.pop(
                    user_id,
                    None
                )

                send_message(
                    chat_id,
                    "✅ کانال با موفقیت اضافه شد.",
                    admin_forcejoin_keyboard()
                )

                return

            # ------------------------------
            # همگانی
            # ------------------------------

            if state == "broadcast":

                admin_states.pop(
                    user_id,
                    None
                )

                send_message(
                    chat_id,
                    "📤 ارسال همگانی شروع شد...\n\n"
                    "بات در حال ارسال پیام برای کاربران است."
                )

                def do_broadcast():

                    success, failed = (
                        broadcast_message(text)
                    )

                    send_message(
                        chat_id,
                        (
                            "✅ <b>همگانی تمام شد</b>\n\n"
                            f"🟢 موفق: <b>{success:,}</b>\n"
                            f"🔴 ناموفق: <b>{failed:,}</b>"
                        ),
                        admin_keyboard()
                    )

                thread = threading.Thread(
                    target=do_broadcast,
                    daemon=True
                )

                thread.start()

                return

    # ======================================
    # /start
    # ======================================

    if text.startswith("/start"):

        # بررسی جوین اجباری
        if not is_admin(user_id):

            if not check_force_join(
                user_id
            ):

                send_message(
                    chat_id,
                    force_join_text(),
                    force_join_keyboard()
                )

                return

        parts = text.split(
            maxsplit=1
        )

        # ------------------------------
        # بررسی لینک دعوت
        # ------------------------------

        if len(parts) == 2:

            payload = parts[1].strip()

            if payload.startswith("ref_"):

                try:

                    referrer_id = int(
                        payload[4:]
                    )

                    create_referral(
                        referrer_id,
                        user_id
                    )

                except ValueError:

                    pass

        # ------------------------------
        # نمایش منو
        # ------------------------------

        send_message(
            chat_id,
            main_text(user_id),
            main_keyboard()
        )

        return


# ==========================================
# پردازش دکمه‌ها
# ==========================================

def handle_callback(callback):

    callback_id = callback.get(
        "id"
    )

    data = callback.get(
        "data"
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

    user = callback.get(
        "from",
        {}
    )

    user_id = user.get(
        "id"
    )

    if callback_id:

        answer_callback_query(
            callback_id
        )

    if (
        not chat_id
        or not message_id
        or not user_id
    ):

        return

    username = user.get(
        "username"
    )

    first_name = user.get(
        "first_name",
        ""
    )

    register_user_activity(
        user_id,
        username,
        first_name
    )

    # ======================================
    # بررسی جوین اجباری
    # ======================================

    if (
        not is_admin(user_id)
        and data != "check_join"
    ):

        if not check_force_join(
            user_id
        ):

            edit_message_text(
                chat_id,
                message_id,
                force_join_text(),
                force_join_keyboard()
            )

            return

    # ======================================
    # بررسی عضویت
    # ======================================

    if data == "check_join":

        if check_force_join(
            user_id
        ):

            edit_message_text(
                chat_id,
                message_id,
                main_text(user_id),
                main_keyboard()
            )

        else:

            edit_message_text(
                chat_id,
                message_id,
                force_join_text(),
                force_join_keyboard()
            )

        return

    # ======================================
    # پنل ادمین
    # ======================================

    if data == "admin_panel":

        if not is_admin(user_id):

            return

        edit_message_text(
            chat_id,
            message_id,
            admin_panel_text(),
            admin_keyboard()
        )

        return

    # ======================================
    # ارزش ژتون
    # ======================================

    if data == "admin_token":

        if not is_admin(user_id):

            return

        admin_states[
            user_id
        ] = "token_value"

        edit_message_text(
            chat_id,
            message_id,
            (
                "🪙 <b>تغییر ارزش ژتون</b>\n\n"
                f"ارزش فعلی: "
                f"<b>{config.TOKEN_VALUE:,}</b> تومان\n\n"
                "مقدار جدید را به عدد بفرست.\n\n"
                "برای لغو بنویس: لغو"
            )
        )

        return

    # ======================================
    # پاداش دعوت
    # ======================================

    if data == "admin_ref":

        if not is_admin(user_id):

            return

        admin_states[
            user_id
        ] = "referrer_reward"

        edit_message_text(
            chat_id,
            message_id,
            (
                "👥 <b>پاداش دعوت‌کننده</b>\n\n"
                f"مقدار فعلی: "
                f"<b>{config.REFERRER_REWARD}</b> ژتون\n\n"
                "مقدار جدید را بفرست."
            )
        )

        return

    # ======================================
    # پاداش دعوت‌شونده
    # ======================================

    if data == "admin_referred":

        if not is_admin(user_id):

            return

        admin_states[
            user_id
        ] = "referred_reward"

        edit_message_text(
            chat_id,
            message_id,
            (
                "🎁 <b>پاداش دعوت‌شونده</b>\n\n"
                f"مقدار فعلی: "
                f"<b>{config.REFERRED_REWARD}</b> ژتون\n\n"
                "مقدار جدید را بفرست."
            )
        )

        return

    # ======================================
    # تنظیمات چرخونه
    # ======================================

    if data == "admin_spin":

        if not is_admin(user_id):

            return

        text = (
            "🎡 <b>تنظیمات چرخونه</b>\n\n"
            f"💰 هزینه هر چرخش: "
            f"<b>{config.SPIN_COST}</b> ژتون\n\n"
            "جوایز فعلی:\n\n"
        )

        for item in config.SPIN_REWARDS:

            text += (
                f"{item['name']} → "
                f"<b>{item['reward']}</b> ژتون\n"
                f"احتمال: <b>{item['chance']}%</b>\n\n"
            )

        edit_message_text(
            chat_id,
            message_id,
            text,
            admin_spin_keyboard()
        )

        return

    # ======================================
    # هزینه چرخونه
    # ======================================

    if data == "admin_spin_cost":

        if not is_admin(user_id):

            return

        admin_states[
            user_id
        ] = "spin_cost"

        edit_message_text(
            chat_id,
            message_id,
            (
                "💰 <b>هزینه چرخونه</b>\n\n"
                f"مقدار فعلی: "
                f"<b>{config.SPIN_COST}</b> ژتون\n\n"
                "مقدار جدید را بفرست."
            )
        )

        return

    # ======================================
    # نمایش جوایز
    # ======================================

    if data == "admin_spin_rewards":

        if not is_admin(user_id):

            return

        text = (
            "🎁 <b>جوایز چرخونه</b>\n\n"
        )

        for index, item in enumerate(
            config.SPIN_REWARDS,
            start=1
        ):

            text += (
                f"{index}. {item['name']}\n"
                f"🪙 جایزه: "
                f"<b>{item['reward']}</b>\n"
                f"🎯 احتمال: "
                f"<b>{item['chance']}%</b>\n\n"
            )

        edit_message_text(
            chat_id,
            message_id,
            text,
            admin_spin_keyboard()
        )

        return

    # ======================================
    # همگانی
    # ======================================

    if data == "admin_broadcast":

        if not is_admin(user_id):

            return

        admin_states[
            user_id
        ] = "broadcast"

        edit_message_text(
            chat_id,
            message_id,
            (
                "📣 <b>ارسال همگانی</b>\n\n"
                "متنی که می‌خوای برای همه "
                "کاربران ارسال بشه رو بفرست.\n\n"
                "برای لغو بنویس: لغو"
            )
        )

        return

    # ======================================
    # جوین اجباری
    # ======================================

    if data == "admin_forcejoin":

        if not is_admin(user_id):

            return

        enabled = getattr(
            config,
            "FORCE_JOIN_ENABLED",
            False
        )

        channels = getattr(
            config,
            "FORCE_JOIN_CHANNELS",
            []
        )

        text = (
            "📢 <b>مدیریت جوین اجباری</b>\n\n"
            f"وضعیت: "
            f"<b>{'فعال 🟢' if enabled else 'خاموش 🔴'}</b>\n\n"
        )

        if channels:

            text += "کانال‌ها:\n"

            for channel in channels:

                text += (
                    f"• <code>{channel}</code>\n"
                )

        else:

            text += (
                "هنوز کانالی اضافه نشده."
            )

        edit_message_text(
            chat_id,
            message_id,
            text,
            admin_forcejoin_keyboard()
        )

        return

    # ======================================
    # افزودن کانال جوین اجباری
    # ======================================

    if data == "force_add":

        if not is_admin(user_id):

            return

        admin_states[
            user_id
        ] = "force_add"

        edit_message_text(
            chat_id,
            message_id,
            (
                "➕ <b>افزودن کانال</b>\n\n"
                "آیدی کانال را بفرست.\n\n"
                "مثال:\n"
                "<code>@mychannel</code>"
            )
        )

        return

    # ======================================
    # حذف کانال جوین اجباری
    # ======================================

    if data.startswith(
        "force_remove_"
    ):

        if not is_admin(user_id):

            return

        try:

            index = int(
                data.replace(
                    "force_remove_",
                    ""
                )
            )

            channels = getattr(
                config,
                "FORCE_JOIN_CHANNELS",
                []
            )

            if (
                0 <= index < len(channels)
            ):

                removed = channels.pop(
                    index
                )

                config.FORCE_JOIN_CHANNELS = (
                    channels
                )

                save_force_join()

                edit_message_text(
                    chat_id,
                    message_id,
                    (
                        "✅ کانال حذف شد:\n"
                        f"<code>{removed}</code>"
                    ),
                    admin_forcejoin_keyboard()
                )

        except Exception:

            pass

        return

    # ======================================
    # روشن / خاموش کردن جوین اجباری
    # ======================================

    if data == "force_toggle":

        if not is_admin(user_id):

            return

        current = getattr(
            config,
            "FORCE_JOIN_ENABLED",
            False
        )

        config.FORCE_JOIN_ENABLED = (
            not current
        )

        save_config_value(
            "FORCE_JOIN_ENABLED",
            config.FORCE_JOIN_ENABLED
        )

        edit_message_text(
            chat_id,
            message_id,
            (
                "✅ وضعیت جوین اجباری تغییر کرد.\n\n"
                f"وضعیت جدید: "
                f"<b>{'فعال 🟢' if config.FORCE_JOIN_ENABLED else 'خاموش 🔴'}</b>"
            ),
            admin_forcejoin_keyboard()
        )

        return

    # ======================================
    # آمار
    # ======================================

    if data == "admin_stats":

        if not is_admin(user_id):

            return

        users_count, tokens, referrals_count = (
            get_admin_stats()
        )

        active = get_active_users()

        text = (
            "📊 <b>آمار ربات</b>\n\n"
            f"👥 کل کاربران: "
            f"<b>{users_count:,}</b>\n\n"
            f"🟢 کاربران فعال: "
            f"<b>{active:,}</b>\n\n"
            f"🪙 مجموع ژتون کاربران: "
            f"<b>{tokens:,}</b>\n\n"
            f"👥 دعوت‌های موفق: "
            f"<b>{referrals_count:,}</b>"
        )

        edit_message_text(
            chat_id,
            message_id,
            text,
            admin_keyboard()
        )

        return

    # ======================================
    # خانه
    # ======================================

    if data == "home":

        edit_message_text(
            chat_id,
            message_id,
            main_text(user_id),
            main_keyboard()
        )

        return

    # ======================================
    # بازی‌ها
    # ======================================

    if data == "games":

        text = (
            "🎮 <b>بازی‌ها</b>\n\n"
            "🎡 <b>چرخونه</b>\n"
            f"هر چرخش: "
            f"<b>{games.SPIN_COST}</b> ژتون\n\n"
            "👇 بازی موردنظرت رو انتخاب کن:"
        )

        edit_message_text(
            chat_id,
            message_id,
            text,
            games_keyboard()
        )

        return

    # ======================================
    # چرخونه
    # ======================================

    if data == "wheel":

        balance = get_balance(
            user_id
        )

        text = (
            "🎡 <b>چرخونه شانس</b>\n\n"
            f"🪙 هزینه هر چرخش: "
            f"<b>{games.SPIN_COST}</b> ژتون\n\n"
            f"💰 موجودی شما: "
            f"<b>{balance}</b> ژتون\n\n"
            "🎁 شاید جایزه ۵۰ ژتونی نصیبت بشه!"
        )

        keyboard = json.dumps({
            "inline_keyboard": [

                [
                    {
                        "text": "🎡 چرخوندن",
                        "callback_data": "spin"
                    }
                ],

                [
                    {
                        "text": "‹ بازگشت",
                        "callback_data": "games"
                    }
                ]

            ]
        })

        edit_message_text(
            chat_id,
            message_id,
            text,
            keyboard
        )

        return

    # ======================================
    # اجرای چرخونه
    # ======================================

    if data == "spin":

        result = spin_wheel(
            user_id
        )

        if not result.get(
            "success"
        ):

            text = result.get(
                "message",
                "❌ خطایی رخ داد."
            )

            keyboard = json.dumps({
                "inline_keyboard": [

                    [
                        {
                            "text": "🎡 بازگشت به چرخونه",
                            "callback_data": "wheel"
                        }
                    ],

                    [
                        {
                            "text": "‹ بازگشت به منو",
                            "callback_data": "home"
                        }
                    ]

                ]
            })

            edit_message_text(
                chat_id,
                message_id,
                text,
                keyboard
            )

            return

        reward = result[
            "reward"
        ]

        name = result[
            "name"
        ]

        new_balance = get_balance(
            user_id
        )

        if reward > 0:

            text = (
                "🎉 <b>برنده شدی!</b>\n\n"
                f"{name}\n\n"
                f"🎁 جایزه: "
                f"<b>{reward}</b> ژتون\n\n"
                f"🪙 موجودی جدید: "
                f"<b>{new_balance}</b> ژتون"
            )

        else:

            text = (
                "😅 <b>این بار پوچ شد!</b>\n\n"
                f"{name}\n\n"
                f"🪙 موجودی جدید: "
                f"<b>{new_balance}</b> ژتون\n\n"
                "دوباره شانست رو امتحان کن! 🎡"
            )

        keyboard = json.dumps({
            "inline_keyboard": [

                [
                    {
                        "text": "🎡 دوباره بچرخون",
                        "callback_data": "spin"
                    }
                ],

                [
                    {
                        "text": "‹ بازگشت",
                        "callback_data": "games"
                    }
                ]

            ]
        })

        edit_message_text(
            chat_id,
            message_id,
            text,
            keyboard
        )

        return

    # ======================================
    # کیف پول
    # ======================================

    if data == "wallet":

        tokens = get_balance(
            user_id
        )

        value = get_balance_value(
            tokens
        )

        text = (
            "🪙 <b>کیف پول شما</b>\n\n"
            f"🪙 موجودی ژتون: "
            f"<b>{tokens:,}</b>\n"
            f"💵 ارزش کل به تومان: "
            f"<b>{value:,}</b>\n\n"
            f"📌 ارزش هر ژتون: "
            f"<b>{config.TOKEN_VALUE:,}</b> تومان"
        )

        edit_message_text(
            chat_id,
            message_id,
            text,
            back_keyboard()
        )

        return

    # ======================================
    # دعوت دوستان
    # ======================================

    if data == "referral":

        text = referral_text(
            user_id
        )

        edit_message_text(
            chat_id,
            message_id,
            text,
            back_keyboard()
        )

        return

    # ======================================
    # حساب کاربری
    # ======================================

    if data == "profile":

        tokens = get_balance(
            user_id
        )

        text = (
            "👤 <b>حساب من</b>\n\n"
            f"🆔 شناسه: "
            f"<code>{user_id}</code>\n\n"
            f"🪙 موجودی ژتون: "
            f"<b>{tokens:,}</b>"
        )

        edit_message_text(
            chat_id,
            message_id,
            text,
            back_keyboard()
        )

        return

    # ======================================
    # جایزه روزانه
    # ======================================

    if data == "daily":

        text = (
            "🎁 <b>جایزه روزانه</b>\n\n"
            "🎁 جایزه روزانه هنوز فعال نشده.\n\n"
            "به‌زودی می‌تونی هر روز جایزه بگیری! ✨"
        )

        edit_message_text(
            chat_id,
            message_id,
            text,
            back_keyboard()
        )

        return

    # ======================================
    # رتبه‌بندی
    # ======================================

    if data == "ranking":

        text = (
            "🏆 <b>رتبه‌بندی</b>\n\n"
            "🥇 رتبه‌بندی به‌زودی فعال می‌شه.\n\n"
            "ببینیم چه کسی بالاترین امتیاز رو می‌گیره! 🔥"
        )

        edit_message_text(
            chat_id,
            message_id,
            text,
            back_keyboard()
        )

        return

    # ======================================
    # تاریخچه
    # ======================================

    if data == "history":

        text = (
            "📜 <b>تاریخچه</b>\n\n"
            "هنوز فعالیتی ثبت نشده."
        )

        edit_message_text(
            chat_id,
            message_id,
            text,
            back_keyboard()
        )

        return

    # ======================================
    # راهنما
    # ======================================

    if data == "help":

        text = (
            "ℹ️ <b>راهنما</b>\n\n"
            "🎮 <b>بازی‌ها</b>\n"
            "مشاهده بازی‌های موجود\n\n"
            "🪙 <b>کیف پول</b>\n"
            "مشاهده موجودی ژتون\n\n"
            "🎁 <b>جایزه روزانه</b>\n"
            "دریافت پاداش روزانه\n\n"
            "👥 <b>دعوت دوستان</b>\n"
            "دریافت ژتون با دعوت دوستان\n\n"
            "👤 <b>حساب من</b>\n"
            "مشاهده اطلاعات حساب"
        )

        edit_message_text(
            chat_id,
            message_id,
            text,
            back_keyboard()
        )

        return


# ==========================================
# اجرای بات
# ==========================================

def run():

    offset = None

    update_runtime_settings()

    print(
        "🚀 BaleBet is running..."
    )

    while True:

        try:

            result = get_updates(
                offset=offset,
                timeout=30
            )

            if not result:

                time.sleep(1)

                continue

            if not result.get(
                "ok"
            ):

                time.sleep(2)

                continue

            updates = result.get(
                "result",
                []
            )

            for update in updates:

                offset = (
                    update["update_id"] + 1
                )

                if "message" in update:

                    handle_message(
                        update["message"]
                    )

                elif "callback_query" in update:

                    handle_callback(
                        update["callback_query"]
                    )

        except Exception as error:

            print(
                f"❌ Error: {error}"
            )

            time.sleep(2)