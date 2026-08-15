# Oura → Telegram Daily Report

Private Python automation that reads Oura API v2 data and posts a daily health summary to Telegram.

## What it does

- Checks at **08:00, 09:00 and 10:00 Europe/Warsaw**.
- Sends only once per day.
- Sends nothing until today's Oura `daily_sleep` document exists, so yesterday's sleep is not presented as today's data.
- Includes Sleep, Readiness, Activity, sleep duration/stages, HRV, lowest sleeping HR, respiratory rate, steps and an approximate 30-day baseline comparison.
- Handles Warsaw CET/CEST automatically.
- Rotates Oura's **single-use OAuth refresh token** automatically after every successful token refresh.

Oura documents that sleep/readiness appear after the ring has synced through the mobile app, while some activity/stress/heart-rate data can update in the background. This project therefore retries later in the morning when 08:00 data is not ready.

## Architecture

```text
Oura Ring
  → Oura mobile app sync
  → Oura Cloud API v2
  → GitHub Actions / Python
  → Telegram Bot API
  → Telegram chat or channel
```

## 1. Create an Oura API application

Open Oura Cloud → API Applications and create an OAuth2 app.

Use scopes:

```text
daily heartrate
```

Register a redirect URI that you control. The URI used during authorization must exactly match one registered in Oura.

## 2. Bootstrap the Oura refresh token

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python scripts/oura_auth.py \
  --client-id YOUR_CLIENT_ID \
  --client-secret YOUR_CLIENT_SECRET \
  --redirect-uri YOUR_REGISTERED_REDIRECT_URI
```

Open the generated URL, authorize the app, then paste the full redirected URL into the terminal. The script prints the initial `OURA_REFRESH_TOKEN`.

> Oura refresh tokens are single-use. Every refresh returns a replacement refresh token and invalidates the previous one. The GitHub workflow therefore writes the replacement back to the repository secret immediately.

## 3. Create a Telegram bot

1. Open `@BotFather` in Telegram and create a bot.
2. Add it to the target group/channel.
3. For a channel, make the bot an administrator with permission to post.
4. Get the target `TELEGRAM_CHAT_ID`. A public channel can often use `@channel_username`; a private channel normally uses a numeric ID such as `-100...`.

## 4. Create the GitHub secrets

Repository → **Settings → Secrets and variables → Actions**.

Add:

```text
OURA_CLIENT_ID
OURA_CLIENT_SECRET
OURA_REFRESH_TOKEN
TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID
GH_SECRET_TOKEN
```

### GH_SECRET_TOKEN

Create a **fine-grained personal access token** limited to this repository with repository permission:

```text
Secrets: Read and write
```

Store that PAT as `GH_SECRET_TOKEN`.

It exists only so the workflow can replace `OURA_REFRESH_TOKEN` after Oura rotates it. The normal `GITHUB_TOKEN` is used for committing `data/last_sent.json` and does not need to be given your personal credentials.

## 5. Test

Run locally without Telegram delivery:

```bash
cp .env.example .env
# Fill the values in .env
DRY_RUN=true python -m src.main
```

For a real local Telegram send:

```bash
DRY_RUN=false python -m src.main
```

In GitHub, use **Actions → Daily Oura Report → Run workflow** for a manual test.

## Daily schedule and duplicate protection

GitHub Actions cron is UTC-only. The workflow runs across the UTC hours that can map to 08:00-10:00 in Warsaw and then checks `Europe/Warsaw` locally, so DST changes do not require editing the cron.

After Telegram delivery, `data/last_sent.json` is committed by `github-actions[bot]`. Later checks that day see the date and exit without sending a duplicate.

If today's sleep has not synced yet at 08:00, no message is sent and no state is recorded. The 09:00 and 10:00 checks can then send the report after you open/sync Oura.

## Example message

```text
OURA DAILY — 16.08.2026

🌙 Sleep: 86
⚡ Readiness: 81
🏃 Activity: 74

Sleep: 7h 42m
Deep: 1h 18m
REM: 1h 51m
Efficiency: 91%

HRV: 48 ms
Lowest HR: 55 bpm
Respiratory rate: 14.2/min
Steps: 8234

vs ~30-day baseline
HRV: ↑ +6.0 ms (good)
Lowest HR: ↓ -2.0 bpm (good)
Sleep: ↑ +21.0 min (good)
```

## Security

- Do not commit `.env` or tokens.
- Keep the repository private because this is personal health automation.
- `data/last_sent.json` stores only the date of the last successful Telegram report, not biometric data.
- The rotated Oura refresh token is written to a temporary runner file and then immediately replaced in GitHub Secrets.

## Development

```bash
pip install -r requirements-dev.txt
pytest -q
```

Project layout:

```text
.github/workflows/daily-oura.yml
src/config.py
src/main.py
src/oura.py
src/report.py
src/state.py
src/telegram.py
scripts/oura_auth.py
tests/test_report.py
data/last_sent.json
```
