from datetime import date, timedelta

from src.report import build_report


def test_report_contains_core_metrics():
    today = date(2026, 8, 16)
    yesterday = today - timedelta(days=1)

    report = build_report(
        today,
        daily_sleep=[{"day": today.isoformat(), "score": 86}],
        daily_readiness=[{"day": today.isoformat(), "score": 81}],
        daily_activity=[{"day": today.isoformat(), "score": 74, "steps": 8234}],
        sleep_docs=[
            {
                "day": yesterday.isoformat(),
                "type": "long_sleep",
                "average_hrv": 42,
                "lowest_heart_rate": 57,
                "total_sleep_duration": 25200,
            },
            {
                "day": today.isoformat(),
                "type": "long_sleep",
                "average_hrv": 48,
                "lowest_heart_rate": 55,
                "average_breath": 14.2,
                "total_sleep_duration": 27720,
                "deep_sleep_duration": 4680,
                "rem_sleep_duration": 6660,
                "efficiency": 91,
            },
        ],
    )

    assert "Sleep: <b>86</b>" in report
    assert "Readiness: <b>81</b>" in report
    assert "Activity: <b>74</b>" in report
    assert "7h 42m" in report
    assert "48 ms" in report
