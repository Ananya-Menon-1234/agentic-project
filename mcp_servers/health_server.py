import json
from pathlib import Path

from fastmcp import FastMCP

mcp = FastMCP("Health Server")


@mcp.tool
def get_health_data(days: int = 7) -> list:
    file_path = Path("data/health.json")
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)
    return data[-days:]


@mcp.tool
def get_health_stats(days: int = 30) -> dict:
    file_path = Path("data/health.json")
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)
    window = data[-days:]

    keys = ["sleep_hours", "steps", "resting_heart_rate", "active_minutes",
             "calories_burned", "stress_score", "mood_score"]

    stats = {}
    for k in keys:
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
def compare_health_trend(days: int = 30) -> dict:
    file_path = Path("data/health.json")
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)
    window = data[-days:]
    mid = len(window) // 2
    first_half, second_half = window[:mid], window[mid:]

    def avg(records, key):
        return round(sum(r[key] for r in records) / len(records), 2)

    keys = ["sleep_hours", "steps", "resting_heart_rate", "active_minutes",
             "stress_score", "mood_score"]

    return {
        "first_half_range": f"{first_half[0]['date']} to {first_half[-1]['date']}",
        "second_half_range": f"{second_half[0]['date']} to {second_half[-1]['date']}",
        "first_half_avg": {k: avg(first_half, k) for k in keys},
        "second_half_avg": {k: avg(second_half, k) for k in keys},
        "change": {k: round(avg(second_half, k) - avg(first_half, k), 2) for k in keys},
    }


if __name__ == "__main__":
    mcp.run(
        transport="http",
        host="127.0.0.1",
        port=8000
    )