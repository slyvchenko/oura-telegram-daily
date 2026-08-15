from __future__ import annotations

from datetime import date
from html import escape
from statistics import mean
from typing import Any, Iterable


def _fmt_duration(seconds: int | float | None) -> str:
    if seconds is None:
        return "—"
    minutes = round(float(seconds) / 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes:02d}m"


def _fmt_num(value: Any, decimals: int = 0, suffix: str = "") -> str:
    if value is None:
        return "—"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return "—"
    rendered = f"{number:.{decimals}f}"
    return f"{rendered}{suffix}"


def _doc_for_day(items: Iterable[dict[str, Any]], day: date) -> dict[str, Any] | None:
    target = day.isoformat()
    docs = [item for item in items if item.get("day") == target]
    if not docs:
        return None
    return docs[-1]


def _main_sleep_for_day(items: Iterable[dict[str, Any]], day: date) -> dict[str, Any] | None:
    target = day.isoformat()
    docs = [item for item in items if item.get("day") == target]
    if not docs:
        return None
    preferred = [item for item in docs if item.get("type") == "long_sleep"]
    candidates = preferred or docs
    return max(candidates, key=lambda item: item.get("total_sleep_duration") or 0)


def _avg(items: Iterable[dict[str, Any]], key: str) -> float | None:
    values: list[float] = []
    for item in items:
        value = item.get(key)
        if value is not None:
            try:
                values.append(float(value))
            except (TypeError, ValueError):
                pass
    return mean(values) if values else None


def _delta(current: float | None, baseline: float | None, unit: str = "", invert: bool = False) -> str:
    if current is None or baseline is None:
        return "—"
    difference = current - baseline
    if abs(difference) < 0.05:
        return "≈ baseline"
    positive_is_good = difference > 0
    if invert:
        positive_is_good = not positive_is_good
    arrow = "↑" if difference > 0 else "↓"
    sign = "+" if difference > 0 else ""
    marker = "good" if positive_is_good else "watch"
    return f"{arrow} {sign}{difference:.1f}{unit} ({marker})"


def build_report(
    day: date,
    daily_sleep: list[dict[str, Any]],
    daily_readiness: list[dict[str, Any]],
    daily_activity: list[dict[str, Any]],
    sleep_docs: list[dict[str, Any]],
) -> str:
    sleep_summary = _doc_for_day(daily_sleep, day) or {}
    readiness = _doc_for_day(daily_readiness, day) or {}
    activity = _doc_for_day(daily_activity, day) or {}
    sleep = _main_sleep_for_day(sleep_docs, day) or {}

    historical_sleep_docs = [
        item
        for item in sleep_docs
        if item.get("day") != day.isoformat() and item.get("type") in {None, "long_sleep"}
    ]
    baseline_hrv = _avg(historical_sleep_docs, "average_hrv")
    baseline_rhr = _avg(historical_sleep_docs, "lowest_heart_rate")
    baseline_sleep = _avg(historical_sleep_docs, "total_sleep_duration")

    current_hrv = sleep.get("average_hrv")
    current_rhr = sleep.get("lowest_heart_rate")
    current_sleep = sleep.get("total_sleep_duration")

    sleep_delta_minutes = None
    baseline_sleep_minutes = None
    if current_sleep is not None and baseline_sleep is not None:
        sleep_delta_minutes = float(current_sleep) / 60
        baseline_sleep_minutes = float(baseline_sleep) / 60

    lines = [
        f"<b>OURA DAILY — {escape(day.strftime('%d.%m.%Y'))}</b>",
        "",
        f"🌙 Sleep: <b>{_fmt_num(sleep_summary.get('score'))}</b>",
        f"⚡ Readiness: <b>{_fmt_num(readiness.get('score'))}</b>",
        f"🏃 Activity: <b>{_fmt_num(activity.get('score'))}</b>",
        "",
        f"Sleep: <b>{_fmt_duration(sleep.get('total_sleep_duration'))}</b>",
        f"Deep: {_fmt_duration(sleep.get('deep_sleep_duration'))}",
        f"REM: {_fmt_duration(sleep.get('rem_sleep_duration'))}",
        f"Efficiency: {_fmt_num(sleep.get('efficiency'), 0, '%')}",
        "",
        f"HRV: <b>{_fmt_num(current_hrv, 0, ' ms')}</b>",
        f"Lowest HR: <b>{_fmt_num(current_rhr, 0, ' bpm')}</b>",
        f"Respiratory rate: {_fmt_num(sleep.get('average_breath'), 1, '/min')}",
        f"Steps: {_fmt_num(activity.get('steps'), 0)}",
        "",
        "<b>vs ~30-day baseline</b>",
        f"HRV: {_delta(float(current_hrv) if current_hrv is not None else None, baseline_hrv, ' ms')}",
        f"Lowest HR: {_delta(float(current_rhr) if current_rhr is not None else None, baseline_rhr, ' bpm', invert=True)}",
        f"Sleep: {_delta(sleep_delta_minutes, baseline_sleep_minutes, ' min')}",
    ]
    return "\n".join(lines)
