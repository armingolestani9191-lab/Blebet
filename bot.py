# ==========================================
# BaleBet - Bot
# ==========================================

import json
import time

import api
import config

from database import (
    init_database,
    get_user_admin_info
)

# ==========================================
# ساخت دیتابیس قبل از لود بازی‌ها
# ==========================================

init_database()

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
    get_balance
)

from referral import (
    create_referral,
    get_referral_count
)

from games import (
    spin_wheel
)


# ==========================================
# تنظیمات عمومی
# ==========================================

POLL_TIMEOUT = 30
POLL_ERROR_SLEEP = 2
UPDATE_ERROR_SLEEP = 1


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
# کیبورد بازگشت
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

def main_text(
    user_id
):

    tokens = get_balance(
        user_id
    )

    active_users = get_active_users()

    return (
        "🎮 <b>BaleBet</b>\n\n"

        "🍀 خوش اومدی!\n\n"

        f"🟢 کاربران فعال: "
        f"<b>{active_users:,}</b> نفر\n\n"

        f"🪙 موجودی ژتون: "
        f"<b>{tokens:,}</b>\n\n"

        "👇 یک گزینه رو انتخاب کن:"
    )


# ==========================================
# ثبت فعالیت کاربر
# ==========================================

def register_user_activity(
    user_id,
    username=None,
    first_name=""
):

    try:

        get_or_create_user(
            user_id,
            username,
            first_name
        )

        update_activity(
            user_id
        )

    except Exception as error:

        print(
            f"❌ User activity error: {error}"
        )


# ==========================================
# بررسی بن بودن کاربر
# ==========================================

def is_user_banned(
    user_id
):

    try:

        user = get_user_admin_info(
            user_id
        )

        if not user:

            return False

        return bool(
            user.get(
                "banned",
                False
            )
        )

    except Exception as error:

        print(
            f"❌ Ban check error: {error}"
        )

        return False


# ==========================================
# بررسی دسترسی کاربر
# ==========================================

def user_is_allowed(
    user_id
):

    if admin.is_admin(
        user_id
    ):

        return True

    if is_user_banned(
        user_id
    ):

        return False

    return True


# ==========================================
# پیام کاربر بن‌شده
# ==========================================

def banned_text():

    return (
        "🚫 <b>دسترسی شما مسدود شده</b>\n\n"
        "دسترسی این حساب توسط مدیریت "
        "به حالت مسدود درآمده است."
    )


# ==========================================
# متن دعوت دوستان
# ==========================================

def referral_text(
    user_id
):

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
# نمایش پیام جوین اجباری
# ==========================================

def show_force_join(
    chat_id
):

    try:

        send_message(
            chat_id,
            admin.force_join_user_text(),
            admin.force_join_user_keyboard()
        )

    except Exception as error:

        print(
            f"❌ Force join send error: {error}"
        )


# ==========================================
# بررسی دسترسی عادی کاربر
# ==========================================

def check_user_access(
    user_id,
    chat_id=None
):

    # ======================================
    # ادمین همیشه دسترسی دارد
    # ======================================

    if admin.is_admin(
        user_id
    ):

        return True

    # ======================================
    # بررسی بن
    # ======================================

    if is_user_banned(
        user_id
    ):

        if chat_id:

            try:

                send_message(
                    chat_id,
                    banned_text()
                )

            except Exception:

                pass

        return False

    # ======================================
    # بررسی جوین اجباری
    # ======================================

    try:

        joined = admin.check_force_join(
            user_id
        )

    except Exception as error:

        print(
            f"❌ Force join check error: {error}"
        )

        joined = False

    if not joined:

        if chat_id:

            show_force_join(
                chat_id
            )

        return False

    return True


# ==========================================
# پردازش پیام
# ==========================================

def handle_message(
    message
):

    if not isinstance(
        message,
        dict
    ):

        return

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

    # ======================================
    # ثبت کاربر و فعالیت
    # ======================================

    register_user_activity(
        user_id,
        username,
        first_name
    )

    # ======================================
    # پنل ادمین
    #
    # حتماً قبل از بن و جوین بررسی می‌شود.
    # ======================================

    try:

        if admin.handle_message(
            message
        ):

            return

    except Exception as error:

        print(
            f"❌ Admin message error: {error}"
        )

        if admin.is_admin(
            user_id
        ):

            try:

                send_message(
                    chat_id,
                    (
                        "❌ خطایی در پنل ادمین رخ داد.\n\n"
                        f"<code>{error}</code>"
                    )
                )

            except Exception:

                pass

        return

    # ======================================
    # بررسی بن
    # ======================================

    if is_user_banned(
        user_id
    ):

        try:

            send_message(
                chat_id,
                banned_text()
            )

        except Exception:

            pass

        return

    # ======================================
    # /start
    # ======================================

    if text.startswith(
        "/start"
    ):

        # ==================================
        # بررسی جوین اجباری
        # ==================================

        if not admin.is_admin(
            user_id
        ):

            try:

                joined = admin.check_force_join(
                    user_id
                )

            except Exception as error:

                print(
                    f"❌ Force join /start error: {error}"
                )

                joined = False

            if not joined:

                show_force_join(
                    chat_id
                )

                return

        # ==================================
        # پردازش پارامتر /start
        # ==================================

        parts = text.split(
            maxsplit=1
        )

        if len(parts) == 2:

            payload = parts[1].strip()

            # ==================================
            # لینک دعوت
            # ==================================

            if payload.startswith(
                "ref_"
            ):

                referrer_text = payload[
                    4:
                ].strip()

                try:

                    referrer_id = int(
                        referrer_text
                    )

                    if (
                        referrer_id != user_id
                    ):

                        create_referral(
                            referrer_id,
                            user_id
                        )

                except (
                    TypeError,
                    ValueError
                ):

                    pass

        # ==================================
        # نمایش منوی اصلی
        # ==================================

        try:

            send_message(
                chat_id,
                main_text(
                    user_id
                ),
                main_keyboard()
            )

        except Exception as error:

            print(
                f"❌ Start message error: {error}"
            )

        return


# ==========================================
# پردازش دکمه‌ها
# ==========================================

def handle_callback(
    callback
):

    if not isinstance(
        callback,
        dict
    ):

        return

    callback_id = callback.get(
        "id"
    )

    data = callback.get(
        "data",
        ""
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

    # ======================================
    # پاسخ سریع به Callback
    # ======================================

    if callback_id:

        try:

            answer_callback_query(
                callback_id
            )

        except Exception as error:

            print(
                f"❌ Callback answer error: {error}"
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

    # ======================================
    # ثبت فعالیت
    # ======================================

    register_user_activity(
        user_id,
        username,
        first_name
    )

    # ======================================
    # پنل ادمین
    #
    # باید قبل از محدودیت جوین بررسی شود.
    # ======================================

    try:

        if admin.handle_callback(
            callback
        ):

            return

    except Exception as error:

        print(
            f"❌ Admin callback error: {error}"
        )

        if admin.is_admin(
            user_id
        ):

            try:

                edit_message_text(
                    chat_id,
                    message_id,
                    (
                        "❌ خطایی در پنل ادمین رخ داد.\n\n"
                        f"<code>{error}</code>"
                    ),
                    admin.admin_back_keyboard()
                )

            except Exception:

                pass

        return

    # ======================================
    # بررسی بن
    # ======================================

    if is_user_banned(
        user_id
    ):

        try:

            edit_message_text(
                chat_id,
                message_id,
                banned_text(),
                back_keyboard()
            )

        except Exception:

            pass

        return

    # ======================================
    # بررسی جوین اجباری
    #
    # خود دکمه check_join مستثنی است
    # چون باید اجازه بدهیم عضویت را بررسی کند.
    # ======================================

    if data != "check_join":

        if not admin.is_admin(
            user_id
        ):

            try:

                joined = admin.check_force_join(
                    user_id
                )

            except Exception as error:

                print(
                    f"❌ Force join callback error: {error}"
                )

                joined = False

            if not joined:

                try:

                    edit_message_text(
                        chat_id,
                        message_id,
                        admin.force_join_user_text(),
                        admin.force_join_user_keyboard()
                    )

                except Exception as error:

                    print(
                        f"❌ Force join edit error: {error}"
                    )

                return

    # ======================================
    # بررسی عضویت
    # ======================================

    if data == "check_join":

        if admin.is_admin(
            user_id
        ):

            joined = True

        else:

            try:

                joined = admin.check_force_join(
                    user_id
                )

            except Exception as error:

                print(
                    f"❌ Check join error: {error}"
                )

                joined = False

        if joined:

            try:

                edit_message_text(
                    chat_id,
                    message_id,
                    main_text(
                        user_id
                    ),
                    main_keyboard()
                )

            except Exception as error:

                print(
                    f"❌ Join success edit error: {error}"
                )

        else:

            try:

                edit_message_text(
                    chat_id,
                    message_id,
                    admin.force_join_user_text(),
                    admin.force_join_user_keyboard()
                )

            except Exception as error:

                print(
                    f"❌ Join failed edit error: {error}"
                )

        return

    # ======================================
    # خانه
    # ======================================

    if data == "home":

        try:

            edit_message_text(
                chat_id,
                message_id,
                main_text(
                    user_id
                ),
                main_keyboard()
            )

        except Exception as error:

            print(
                f"❌ Home error: {error}"
            )

        return

    # ======================================
    # بازی‌ها
    # ======================================

    if data == "games":

        try:

            spin_cost = games.get_spin_cost()

            text = (
                "🎮 <b>بازی‌ها</b>\n\n"

                "🎡 <b>چرخونه</b>\n\n"

                f"🪙 هزینه هر چرخش: "
                f"<b>{spin_cost:,}</b> ژتون\n\n"

                "👇 بازی موردنظرت رو انتخاب کن:"
            )

            edit_message_text(
                chat_id,
                message_id,
                text,
                games_keyboard()
            )

        except Exception as error:

            print(
                f"❌ Games menu error: {error}"
            )

        return

    # ======================================
    # چرخونه
    # ======================================

    if data == "wheel":

        try:

            balance = get_balance(
                user_id
            )

            spin_cost = games.get_spin_cost()

            text = (
                "🎡 <b>چرخونه شانس</b>\n\n"

                f"🪙 هزینه هر چرخش: "
                f"<b>{spin_cost:,}</b> ژتون\n\n"

                f"🪙 موجودی شما: "
                f"<b>{balance:,}</b> ژتون\n\n"

                "🎁 آماده‌ای؟"
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

        except Exception as error:

            print(
                f"❌ Wheel menu error: {error}"
            )

        return

    # ======================================
    # اجرای چرخونه
    # ======================================

    if data == "spin":

        try:

            result = spin_wheel(
                user_id
            )

        except Exception as error:

            print(
                f"❌ Spin error: {error}"
            )

            result = {
                "success": False,
                "message": (
                    "❌ هنگام اجرای بازی خطایی رخ داد."
                )
            }

        if not isinstance(
            result,
            dict
        ):

            result = {
                "success": False,
                "message": (
                    "❌ پاسخ نامعتبر از بازی دریافت شد."
                )
            }

        if not result.get(
            "success",
            False
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

            try:

                edit_message_text(
                    chat_id,
                    message_id,
                    text,
                    keyboard
                )

            except Exception as error:

                print(
                    f"❌ Spin result edit error: {error}"
                )

            return

        try:

            reward = int(
                result.get(
                    "reward",
                    0
                )
            )

        except (
            TypeError,
            ValueError
        ):

            reward = 0

        name = str(
            result.get(
                "name",
                "نتیجه بازی"
            )
        )

        new_balance = get_balance(
            user_id
        )

        if reward > 0:

            text = (
                "🎉 <b>برنده شدی!</b>\n\n"

                f"{name}\n\n"

                f"🎁 جایزه: "
                f"<b>{reward:,}</b> ژتون\n\n"

                f"🪙 موجودی جدید: "
                f"<b>{new_balance:,}</b> ژتون"
            )

        else:

            text = (
                "😅 <b>این بار چیزی نبردی!</b>\n\n"

                f"{name}\n\n"

                f"🪙 موجودی جدید: "
                f"<b>{new_balance:,}</b> ژتون\n\n"

                "دوباره امتحان کن! 🎡"
            )

        keyboard = json.dumps({
            "inline_keyboard": [

                [
                    {
                        "text": "🎡 دوباره بازی کن",
                        "callback_data": "spin"
                    }
                ],

                [
                    {
                        "text": "‹ بازگشت به بازی‌ها",
                        "callback_data": "games"
                    }
                ],

                [
                    {
                        "text": "🏠 منوی اصلی",
                        "callback_data": "home"
                    }
                ]

            ]
        })

        try:

            edit_message_text(
                chat_id,
                message_id,
                text,
                keyboard
            )

        except Exception as error:

            print(
                f"❌ Spin result error: {error}"
            )

        return

    # ======================================
    # کیف پول
    # ======================================

    if data == "wallet":

        try:

            tokens = get_balance(
                user_id
            )

            text = (
                "🪙 <b>کیف پول بازی</b>\n\n"

                f"🪙 موجودی ژتون:\n"
                f"<b>{tokens:,}</b>\n\n"

                "ℹ️ ژتون‌ها فقط واحد داخل بازی "
                "هستند و ارزش واقعی ندارند."
            )

            edit_message_text(
                chat_id,
                message_id,
                text,
                back_keyboard()
            )

        except Exception as error:

            print(
                f"❌ Wallet error: {error}"
            )

        return

    # ======================================
    # دعوت دوستان
    # ======================================

    if data == "referral":

        try:

            text = referral_text(
                user_id
            )

            edit_message_text(
                chat_id,
                message_id,
                text,
                back_keyboard()
            )

        except Exception as error:

            print(
                f"❌ Referral error: {error}"
            )

        return

    # ======================================
    # حساب کاربری
    # ======================================

    if data == "profile":

        try:

            tokens = get_balance(
                user_id
            )

            text = (
                "👤 <b>حساب من</b>\n\n"

                f"🆔 شناسه:\n"
                f"<code>{user_id}</code>\n\n"

                f"🪙 موجودی ژتون:\n"
                f"<b>{tokens:,}</b>"
            )

            edit_message_text(
                chat_id,
                message_id,
                text,
                back_keyboard()
            )

        except Exception as error:

            print(
                f"❌ Profile error: {error}"
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

        try:

            edit_message_text(
                chat_id,
                message_id,
                text,
                back_keyboard()
            )

        except Exception as error:

            print(
                f"❌ Daily error: {error}"
            )

        return

    # ======================================
    # رتبه‌بندی
    # ======================================

    if data == "ranking":

        text = (
            "🏆 <b>رتبه‌بندی</b>\n\n"

            "🥇 رتبه‌بندی به‌زودی فعال می‌شه.\n\n"

            "ببینیم چه کسی بالاترین امتیاز "
            "رو می‌گیره! 🔥"
        )

        try:

            edit_message_text(
                chat_id,
                message_id,
                text,
                back_keyboard()
            )

        except Exception as error:

            print(
                f"❌ Ranking error: {error}"
            )

        return

    # ======================================
    # تاریخچه
    # ======================================

    if data == "history":

        try:

            transactions = wallet.get_transactions(
                user_id,
                10
            )

        except Exception as error:

            print(
                f"❌ History load error: {error}"
            )

            transactions = []

        if not transactions:

            text = (
                "📜 <b>تاریخچه</b>\n\n"
                "هنوز فعالیتی ثبت نشده."
            )

        else:

            text = (
                "📜 <b>تاریخچه ژتون‌ها</b>\n\n"
            )

            for item in transactions:

                try:

                    amount = int(
                        item.get(
                            "amount",
                            0
                        )
                    )

                except (
                    TypeError,
                    ValueError
                ):

                    amount = 0

                reason = str(
                    item.get(
                        "reason",
                        "فعالیت"
                    )
                )

                created_at = str(
                    item.get(
                        "created_at",
                        ""
                    )
                )

                if amount >= 0:

                    sign = "+"

                else:

                    sign = ""

                text += (
                    f"🪙 <b>{sign}{amount:,}</b>\n"
                    f"📝 {reason}\n"
                    f"🕐 {created_at}\n\n"
                )

        try:

            edit_message_text(
                chat_id,
                message_id,
                text,
                back_keyboard()
            )

        except Exception as error:

            print(
                f"❌ History error: {error}"
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
            "مشاهده ژتون‌های داخل بازی\n\n"

            "🎁 <b>جایزه روزانه</b>\n"
            "دریافت پاداش روزانه\n\n"

            "👥 <b>دعوت دوستان</b>\n"
            "دریافت ژتون با دعوت دوستان\n\n"

            "👤 <b>حساب من</b>\n"
            "مشاهده اطلاعات حساب"
        )

        try:

            edit_message_text(
                chat_id,
                message_id,
                text,
                back_keyboard()
            )

        except Exception as error:

            print(
                f"❌ Help error: {error}"
            )

        return

    # ======================================
    # Callback ناشناخته
    # ======================================

    print(
        f"⚠️ Unknown callback: {data}"
    )


# ==========================================
# پردازش یک Update
# ==========================================

def process_update(
    update
):

    if not isinstance(
        update,
        dict
    ):

        return

    try:

        if "message" in update:

            handle_message(
                update["message"]
            )

            return

        if "callback_query" in update:

            handle_callback(
                update["callback_query"]
            )

            return

    except Exception as error:

        print(
            f"❌ Update processing error: {error}"
        )


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
                timeout=POLL_TIMEOUT
            )

            # ==================================
            # پاسخ نامعتبر یا None
            # ==================================

            if not result:

                time.sleep(
                    POLL_ERROR_SLEEP
                )

                continue

            # ==================================
            # خطای API
            # ==================================

            if not result.get(
                "ok",
                False
            ):

                print(
                    "⚠️ getUpdates returned an error."
                )

                time.sleep(
                    POLL_ERROR_SLEEP
                )

                continue

            updates = result.get(
                "result",
                []
            )

            if not isinstance(
                updates,
                list
            ):

                time.sleep(
                    POLL_ERROR_SLEEP
                )

                continue

            # ==================================
            # پردازش آپدیت‌ها
            # ==================================

            for update in updates:

                if not isinstance(
                    update,
                    dict
                ):

                    continue

                update_id = update.get(
                    "update_id"
                )

                # ==================================
                # Offset را قبل از پردازش بعدی تنظیم کن
                # ==================================

                if update_id is not None:

                    try:

                        offset = (
                            int(update_id) + 1
                        )

                    except (
                        TypeError,
                        ValueError
                    ):

                        pass

                # ==================================
                # هر آپدیت جداگانه محافظت شود
                # ==================================

                try:

                    process_update(
                        update
                    )

                except Exception as error:

                    print(
                        f"❌ Single update error: {error}"
                    )

                    time.sleep(
                        UPDATE_ERROR_SLEEP
                    )

        except KeyboardInterrupt:

            print(
                "🛑 Bot stopped."
            )

            break

        except Exception as error:

            print(
                f"❌ Main loop error: {error}"
            )

            time.sleep(
                POLL_ERROR_SLEEP
            )


# ==========================================
# اجرای مستقیم فایل
# ==========================================

if __name__ == "__main__":

    run()
