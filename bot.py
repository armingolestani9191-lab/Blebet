# ==========================================
# BaleBet - Bot
# ==========================================

import json
import time

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

from config import TOKEN_VALUE


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
                    "text": "👤 حساب من",
                    "callback_data": "profile"
                }
            ],
            [
                {
                    "text": "🏆 رتبه‌بندی",
                    "callback_data": "ranking"
                },
                {
                    "text": "📜 تاریخچه",
                    "callback_data": "history"
                }
            ],
            [
                {
                    "text": "ℹ️ راهنما",
                    "callback_data": "help"
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

    tokens = get_balance(user_id)

    value = get_balance_value(tokens)

    active_users = get_active_users()

    return (
        "🎰 <b>BaleBet</b>\n\n"
        "🍀 خوش اومدی! شانس با توئه.\n\n"
        f"🟢 کاربران درحال بازی: <b>{active_users:,}</b> نفر\n\n"
        f"🪙 موجودی ژتون: <b>{tokens:,}</b>\n"
        f"💵 ارزش کل به تومان: <b>{value:,}</b>\n\n"
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

    update_activity(user_id)


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

    chat_id = chat.get("id")

    user_id = user.get("id")

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
    # /start
    # ======================================

    if text.startswith("/start"):

        send_message(
            chat_id,
            main_text(user_id),
            main_keyboard()
        )


# ==========================================
# پردازش دکمه‌ها
# ==========================================

def handle_callback(callback):

    callback_id = callback.get("id")

    data = callback.get("data")

    message = callback.get(
        "message",
        {}
    )

    chat = message.get(
        "chat",
        {}
    )

    chat_id = chat.get("id")

    message_id = message.get(
        "message_id"
    )

    user = callback.get(
        "from",
        {}
    )

    user_id = user.get("id")

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

    # ======================================
    # ثبت فعالیت
    # ======================================

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
    # کیف پول
    # ======================================

    if data == "wallet":

        tokens = get_balance(user_id)

        value = get_balance_value(
            tokens
        )

        text = (
            "🪙 <b>کیف پول شما</b>\n\n"
            f"🪙 موجودی ژتون: <b>{tokens:,}</b>\n"
            f"💵 ارزش کل به تومان: <b>{value:,}</b>\n\n"
            f"📌 ارزش هر ژتون: "
            f"<b>{TOKEN_VALUE:,}</b> تومان"
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

        tokens = get_balance(user_id)

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
    # بازی‌ها
    # ======================================

    if data == "games":

        text = (
            "🎮 <b>بازی‌ها</b>\n\n"
            "🎲 بازی‌ها به‌زودی اینجا قرار می‌گیرن.\n\n"
            "منتظر اولین بازی باش! 🔥"
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

    print("🚀 BaleBet is running...")

    while True:

        try:

            result = get_updates(
                offset=offset,
                timeout=30
            )

            if not result:

                time.sleep(1)

                continue

            if not result.get("ok"):

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