from __future__ import annotations

import requests


class TelegramError(RuntimeError):
    pass


def send_message(bot_token: str, chat_id: str, text: str, timeout: int = 30) -> None:
    response = requests.post(
        f"https://api.telegram.org/bot{bot_token}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        },
        timeout=timeout,
    )
    if not response.ok:
        raise TelegramError(f"Telegram sendMessage failed ({response.status_code}): {response.text[:500]}")
