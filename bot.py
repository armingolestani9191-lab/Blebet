# ==========================================
# BaleBet - Bot
# ==========================================

import json
import time

import api
import config
import games
import referral
import wallet
import admin

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
        f"<b>{referral.get_referrer_reward()}</b> ژتون\n"

        f"🎁 پاداش دوستت: "
        f"<b>{referral.get_referred_reward()}</b> ژتون\n\n"

        f"👥 تعداد دعوت‌های موفق: "
        f"<b>{count}</b>\n\n"

        "🔗 لینک دعوت اختصاصی شما:\n"
        "<code>لینک در تنظیمات بات قرار می‌گیرد</code>"
    )


# ==========================================
# بررسی عضویت کاربر
# ==========================================

def check_force_join(user_id):

    from database import (
        get_bool_setting,
        get_force_join_channels
    )

    enabled = get_bool_setting(
        "force_join_enabled",
        False
    )

    if not enabled:

        return True

    channels = get_force_join_channels()

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

    from database import (
        get_force_join_channels
    )

    channels = get_force_join_channels()

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

    from database import (
        get_force_join_channels
    )

    channels = get_force_join_channels()

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
    # انتقال کامل پنل ادمین
    # ======================================

    if admin.handle_message(
        message
    ):

        return

    # ======================================
    # /start
    # ======================================

    if text.startswith("/start"):

        # بررسی جوین اجباری

        if not admin.is_admin(
            user_id
        ):

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

            if payload.startswith(
                "ref_"
            ):

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
    # انتقال کامل Callbackهای پنل
    # ======================================

    if admin.handle_callback(
        callback
    ):

        return

    # ======================================
    # بررسی جوین اجباری
    # ======================================

    if data != "check_join":

        if not admin.is_admin(
            user_id
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
                        "text": "‹ بازگشت به منو",
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

                time.sleep(
                    1
                )

                continue

            if not result.get(
                "ok"
            ):

                time.sleep(
                    2
                )

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

            time.sleep(
                2
    )
