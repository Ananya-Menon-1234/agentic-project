import json
from pathlib import Path

from fastmcp import FastMCP

mcp = FastMCP("Health Server")

STAT_KEYS = ["sleep_hours", "steps", "resting_heart_rate", "active_minutes",
             "calories_burned", "stress_score", "mood_score"]


def _load() -> list[dict]:
    with open(Path("data/health.json"), "r", encoding="utf-8") as f:
        return json.load(f)


def _window(days: int = 30, start_date: str = "", end_date: str = "") -> list[dict]:
    """If a date is given, filter by it. Otherwise take the most recent `days`."""
    data = _load()
    if start_date or end_date:
        lo = start_date or "0000-01-01"
        hi = end_date or "9999-12-31"
        return [r for r in data if lo <= r["date"] <= hi]  # ISO dates sort as text
    return data[-days:]


def _avg(records: list[dict], key: str) -> float:
    return round(sum(r[key] for r in records) / len(records), 2)


def _no_data(start_date: str = "", end_date: str = "") -> dict:
    data = _load()
    return {
        "error": f"No health data between {start_date or 'start'} and {end_date or 'end'}.",
        "available_range": f"{data[0]['date']} to {data[-1]['date']}",
    }


@mcp.tool
def get_health_data(days: int = 7, start_date: str = "", end_date: str = "") -> list:
    """Raw daily health records. Use `days` for the most recent N days, or
    start_date/end_date (YYYY-MM-DD) for a specific period. Prefer
    get_health_stats for summaries."""
    window = _window(days, start_date, end_date)
    return window if window else [_no_data(start_date, end_date)]


@mcp.tool
def get_health_stats(days: int = 30, start_date: str = "", end_date: str = "") -> dict:
    """Average, min and max of each health metric. Use `days` for recent
    windows, or start_date/end_date (YYYY-MM-DD) for a named period such as
    a specific month."""
    window = _window(days, start_date, end_date)
    if not window:
        return _no_data(start_date, end_date)
    stats = {
        k: {
            "avg": _avg(window, k),
            "min": min(r[k] for r in window),
            "max": max(r[k] for r in window),
        }
        for k in STAT_KEYS
    }
    return {
        "period_days": len(window),
        "date_range": f"{window[0]['date']} to {window[-1]['date']}",
        "stats": stats,
    }


@mcp.tool
def compare_health_trend(days: int = 30, start_date: str = "", end_date: str = "") -> dict:
    """Compare the first half of a period against the second half, to see
    whether things improved or worsened within it."""
    window = _window(days, start_date, end_date)
    if len(window) < 2:
        return _no_data(start_date, end_date)
    mid = len(window) // 2
    first, second = window[:mid], window[mid:]
    return {
        "first_half_range": f"{first[0]['date']} to {first[-1]['date']}",
        "second_half_range": f"{second[0]['date']} to {second[-1]['date']}",
        "first_half_avg": {k: _avg(first, k) for k in STAT_KEYS},
        "second_half_avg": {k: _avg(second, k) for k in STAT_KEYS},
        "change": {k: round(_avg(second, k) - _avg(first, k), 2) for k in STAT_KEYS},
    }


@mcp.tool
def compare_health_periods(start_a: str, end_a: str, start_b: str, end_b: str) -> dict:
    """Compare two separate periods, for example April vs July. Dates are
    YYYY-MM-DD. The change is period B minus period A."""
    a = _window(start_date=start_a, end_date=end_a)
    b = _window(start_date=start_b, end_date=end_b)
    if not a or not b:
        return _no_data()
    return {
        "period_a": f"{a[0]['date']} to {a[-1]['date']}",
        "period_b": f"{b[0]['date']} to {b[-1]['date']}",
        "period_a_avg": {k: _avg(a, k) for k in STAT_KEYS},
        "period_b_avg": {k: _avg(b, k) for k in STAT_KEYS},
        "change_b_minus_a": {k: round(_avg(b, k) - _avg(a, k), 2) for k in STAT_KEYS},
    }


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)