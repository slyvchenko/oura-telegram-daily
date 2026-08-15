from __future__ import annotations

import logging
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

from src.config import Config
from src.oura import OuraClient
from src.report import build_report
from src.state import StateStore
from src.telegram import send_message


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def _persist_rotated_refresh_token(path: str | None, token: str) -> None:
    if not path:
        return
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(token, encoding="utf-8")


def main() -> int:
    load_dotenv()
    config = Config.from_env()
    now = datetime.now(ZoneInfo(config.timezone))
    today = now.date()

    state = StateStore()
    if state.last_sent_date() == today:
        log.info("Today's report has already been sent; nothing to do.")
        return 0

    client = OuraClient(
        client_id=config.oura_client_id,
        client_secret=config.oura_client_secret,
        refresh_token=config.oura_refresh_token,
    )
    tokens = client.refresh_access_token()
    _persist_rotated_refresh_token(config.refresh_token_file, tokens.refresh_token)
    log.info("Oura OAuth token refreshed successfully.")

    history_start = today - timedelta(days=35)
    daily_sleep = client.daily_sleep(history_start, today)

    if not any(item.get("day") == today.isoformat() for item in daily_sleep):
        log.info("Today's Oura sleep summary is not synced yet; report will not be sent.")
        return 0

    daily_readiness = client.daily_readiness(history_start, today)
    daily_activity = client.daily_activity(history_start, today)
    sleep_docs = client.sleep(history_start, today)

    report = build_report(today, daily_sleep, daily_readiness, daily_activity, sleep_docs)

    if config.dry_run:
        print(report)
        log.info("DRY_RUN=true, Telegram message was not sent.")
        return 0

    send_message(config.telegram_bot_token, config.telegram_chat_id, report)
    state.mark_sent(today)
    log.info("Daily report sent to Telegram and state updated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
