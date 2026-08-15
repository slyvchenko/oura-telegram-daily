from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    oura_client_id: str
    oura_client_secret: str
    oura_refresh_token: str
    telegram_bot_token: str
    telegram_chat_id: str
    timezone: str = "Europe/Warsaw"
    dry_run: bool = False
    refresh_token_file: str | None = None

    @classmethod
    def from_env(cls) -> "Config":
        required = {
            "OURA_CLIENT_ID": os.getenv("OURA_CLIENT_ID"),
            "OURA_CLIENT_SECRET": os.getenv("OURA_CLIENT_SECRET"),
            "OURA_REFRESH_TOKEN": os.getenv("OURA_REFRESH_TOKEN"),
            "TELEGRAM_BOT_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN"),
            "TELEGRAM_CHAT_ID": os.getenv("TELEGRAM_CHAT_ID"),
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

        return cls(
            oura_client_id=required["OURA_CLIENT_ID"] or "",
            oura_client_secret=required["OURA_CLIENT_SECRET"] or "",
            oura_refresh_token=required["OURA_REFRESH_TOKEN"] or "",
            telegram_bot_token=required["TELEGRAM_BOT_TOKEN"] or "",
            telegram_chat_id=required["TELEGRAM_CHAT_ID"] or "",
            timezone=os.getenv("TIMEZONE", "Europe/Warsaw"),
            dry_run=os.getenv("DRY_RUN", "false").lower() in {"1", "true", "yes"},
            refresh_token_file=os.getenv("OURA_REFRESH_TOKEN_FILE") or None,
        )
