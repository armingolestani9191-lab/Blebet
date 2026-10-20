# ==========================================
# BaleBet - Bale API
# ==========================================

import requests

from config import BOT_TOKEN


BASE_URL = f"https://tapi.bale.ai/bot{BOT_TOKEN}"


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


def get_updates(offset=None, timeout=30):
    data = {
        "timeout": timeout
    }

    if offset is not None:
        data["offset"] = offset

    return api_request(
        "getUpdates",
        data
    )


def send_message(chat_id, text, reply_markup=None):
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


def answer_callback_query(callback_query_id):
    return api_request(
        "answerCallbackQuery",
        {
            "callback_query_id": callback_query_id
        }
    )