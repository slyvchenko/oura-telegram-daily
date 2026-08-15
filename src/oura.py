from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

import requests


API_BASE = "https://api.ouraring.com/v2/usercollection"
TOKEN_URL = "https://api.ouraring.com/oauth/token"


class OuraError(RuntimeError):
    pass


@dataclass(frozen=True)
class OAuthTokens:
    access_token: str
    refresh_token: str
    expires_in: int | None = None


class OuraClient:
    def __init__(self, client_id: str, client_secret: str, refresh_token: str, timeout: int = 30):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.timeout = timeout
        self.access_token: str | None = None

    def refresh_access_token(self) -> OAuthTokens:
        response = requests.post(
            TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
            timeout=self.timeout,
        )
        if not response.ok:
            raise OuraError(f"Oura OAuth refresh failed ({response.status_code}): {response.text[:500]}")

        payload = response.json()
        try:
            tokens = OAuthTokens(
                access_token=payload["access_token"],
                refresh_token=payload["refresh_token"],
                expires_in=payload.get("expires_in"),
            )
        except KeyError as exc:
            raise OuraError(f"Oura OAuth response is missing {exc.args[0]}") from exc

        self.access_token = tokens.access_token
        self.refresh_token = tokens.refresh_token
        return tokens

    def _get(self, endpoint: str, **params: str) -> list[dict[str, Any]]:
        if not self.access_token:
            raise OuraError("Access token is not initialized")

        response = requests.get(
            f"{API_BASE}/{endpoint}",
            headers={"Authorization": f"Bearer {self.access_token}"},
            params=params,
            timeout=self.timeout,
        )
        if not response.ok:
            raise OuraError(f"Oura API {endpoint} failed ({response.status_code}): {response.text[:500]}")

        payload = response.json()
        data = payload.get("data", [])
        if not isinstance(data, list):
            raise OuraError(f"Unexpected response from Oura endpoint {endpoint}")
        return data

    def daily_sleep(self, start: date, end: date) -> list[dict[str, Any]]:
        return self._get("daily_sleep", start_date=start.isoformat(), end_date=end.isoformat())

    def daily_readiness(self, start: date, end: date) -> list[dict[str, Any]]:
        return self._get("daily_readiness", start_date=start.isoformat(), end_date=end.isoformat())

    def daily_activity(self, start: date, end: date) -> list[dict[str, Any]]:
        return self._get("daily_activity", start_date=start.isoformat(), end_date=end.isoformat())

    def sleep(self, start: date, end: date) -> list[dict[str, Any]]:
        return self._get("sleep", start_date=start.isoformat(), end_date=end.isoformat())
