# ==========================================
# BaleBet - Bale API
# ==========================================

import requests

from config import BOT_TOKEN


# ==========================================
# تنظیمات API
# ==========================================

BASE_URL = f"https://tapi.bale.ai/bot{BOT_TOKEN}"


# ==========================================
# درخواست عمومی API
# ==========================================

def api_request(method, data=None):

    url = f"{BASE_URL}/{method}"

    try:

        response = requests.post(
            url,
            data=data,
            timeout=15
        )

        response.raise_for_status()

        return response.json()

    except requests.RequestException:

        return None

    except ValueError:

        return None


# ==========================================
# دریافت آپدیت‌ها
# ==========================================

def get_updates(
    offset=None,
    timeout=30
):

    data = {
        "timeout": timeout
    }

    if offset is not None:

        data["offset"] = offset

    return api_request(
        "getUpdates",
        data
    )


# ==========================================
# ارسال پیام
# ==========================================

def send_message(
    chat_id,
    text,
    reply_markup=None
):

    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }

    if reply_markup:

        data["reply_markup"] = reply_markup

    return api_request(
        "sendMessage",
        data
    )


# ==========================================
# فوروارد پیام
# ==========================================

def forward_message(
    chat_id,
    from_chat_id,
    message_id
):

    return api_request(
        "forwardMessage",
        {
            "chat_id": chat_id,
            "from_chat_id": from_chat_id,
            "message_id": message_id
        }
    )


# ==========================================
# کپی پیام
# ==========================================

def copy_message(
    chat_id,
    from_chat_id,
    message_id
):

    return api_request(
        "copyMessage",
        {
            "chat_id": chat_id,
            "from_chat_id": from_chat_id,
            "message_id": message_id
        }
    )


# ==========================================
# ویرایش پیام
# ==========================================

def edit_message_text(
    chat_id,
    message_id,
    text,
    reply_markup=None
):

    data = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": "HTML"
    }

    if reply_markup:

        data["reply_markup"] = reply_markup

    return api_request(
        "editMessageText",
        data
    )


# ==========================================
# حذف پیام
# ==========================================

def delete_message(
    chat_id,
    message_id
):

    return api_request(
        "deleteMessage",
        {
            "chat_id": chat_id,
            "message_id": message_id
        }
    )


# ==========================================
# پاسخ به Callback
# ==========================================

def answer_callback_query(
    callback_query_id,
    text=None,
    show_alert=False
):

    data = {
        "callback_query_id": callback_query_id,
        "show_alert": show_alert
    }

    if text:

        data["text"] = text

    return api_request(
        "answerCallbackQuery",
        data
    )


# ==========================================
# بررسی عضویت کاربر در کانال
# ==========================================

def get_chat_member(
    chat_id,
    user_id
):

    return api_request(
        "getChatMember",
        {
            "chat_id": chat_id,
            "user_id": user_id
        }
    )


# ==========================================
# دریافت اطلاعات کانال
# ==========================================

def get_chat(
    chat_id
):

    return api_request(
        "getChat",
        {
            "chat_id": chat_id
        }
    )


# ==========================================
# دریافت تعداد اعضای کانال
# ==========================================

def get_chat_member_count(
    chat_id
):

    return api_request(
        "getChatMemberCount",
        {
            "chat_id": chat_id
        }
    )


# ==========================================
# ارسال اکشن
# ==========================================

def send_chat_action(
    chat_id,
    action
):

    return api_request(
        "sendChatAction",
        {
            "chat_id": chat_id,
            "action": action
        }
    )


# ==========================================
# دریافت اطلاعات خود بات
# ==========================================

def get_me():

    return api_request(
        "getMe"
    )
