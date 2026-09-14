import json
from pathlib import Path

from fastmcp import FastMCP

mcp = FastMCP("Productivity Server")

METRIC_KEYS = ["focus_score", "deep_work_hours", "tasks_completed",
               "meetings_hours", "context_switches", "burnout_risk_score"]


def _load():
    file_path = Path("data/productivity.json")
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


@mcp.tool
def get_productivity_data(days: int = 7) -> list:
    return _load()[-days:]


@mcp.tool
def get_productivity_stats(days: int = 30) -> dict:
    window = _load()[-days:]

    stats = {}
    for k in METRIC_KEYS:
        values = [r[k] for r in window]
        stats[k] = {
            "avg": round(sum(values) / len(values), 2),
            "min": min(values),
            "max": max(values),
        }

    return {
        "period_days": len(window),
        "date_range": f"{window[0]['date']} to {window[-1]['date']}",
        "stats": stats,
    }


@mcp.tool
def compare_productivity_trend(days: int = 30) -> dict:
    window = _load()[-days:]
    mid = len(window) // 2
    first_half, second_half = window[:mid], window[mid:]

    def avg(records, key):
        return round(sum(r[key] for r in records) / len(records), 2)

    return {
        "first_half_range": f"{first_half[0]['date']} to {first_half[-1]['date']}",
        "second_half_range": f"{second_half[0]['date']} to {second_half[-1]['date']}",
        "first_half_avg": {k: avg(first_half, k) for k in METRIC_KEYS},
        "second_half_avg": {k: avg(second_half, k) for k in METRIC_KEYS},
        "change": {k: round(avg(second_half, k) - avg(first_half, k), 2) for k in METRIC_KEYS},
    }


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8002)