from __future__ import annotations

import argparse
import secrets
from urllib.parse import parse_qs, urlencode, urlparse

import requests


AUTHORIZE_URL = "https://cloud.ouraring.com/oauth/authorize"
TOKEN_URL = "https://api.ouraring.com/oauth/token"


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap an Oura OAuth2 refresh token.")
    parser.add_argument("--client-id", required=True)
    parser.add_argument("--client-secret", required=True)
    parser.add_argument("--redirect-uri", required=True)
    args = parser.parse_args()

    state = secrets.token_urlsafe(24)
    params = {
        "response_type": "code",
        "client_id": args.client_id,
        "redirect_uri": args.redirect_uri,
        "scope": "daily heartrate",
        "state": state,
    }
    print("Open this URL in your browser:\n")
    print(f"{AUTHORIZE_URL}?{urlencode(params)}\n")
    redirected = input("Paste the full URL you were redirected to: ").strip()
    parsed = urlparse(redirected)
    query = parse_qs(parsed.query)

    if query.get("state", [None])[0] != state:
        raise RuntimeError("OAuth state mismatch")
    if "error" in query:
        raise RuntimeError(f"Oura authorization failed: {query['error'][0]}")
    code = query.get("code", [None])[0]
    if not code:
        raise RuntimeError("No authorization code found in redirected URL")

    response = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "client_id": args.client_id,
            "client_secret": args.client_secret,
            "redirect_uri": args.redirect_uri,
        },
        timeout=30,
    )
    response.raise_for_status()
    tokens = response.json()

    print("\nAdd this value to GitHub Secret OURA_REFRESH_TOKEN:\n")
    print(tokens["refresh_token"])
    print("\nDo not commit it to git.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
