import json
import math
import os
import random
from datetime import date, timedelta

random.seed(42)

START = date(2026, 4, 1)
END = date(2026, 10, 25)

dates = []
d = START
while d <= END:
    dates.append(d)
    d += timedelta(days=1)
n = len(dates)

ALL = {"health", "finance", "productivity"}


PATCHES = [
    (date(2026, 4, 21), date(2026, 5, 1),  -1.0, ALL),
    (date(2026, 5, 20), date(2026, 6, 2),  -1.2, {"finance"}),
    (date(2026, 6, 10), date(2026, 6, 20), -1.1, ALL),
    (date(2026, 7, 1),  date(2026, 7, 10), -1.2, {"health"}),
    (date(2026, 8, 3),  date(2026, 8, 14), -1.2, ALL),
    (date(2026, 9, 1),  date(2026, 9, 10), -1.1, {"productivity"}),
    (date(2026, 10, 12), date(2026, 10, 21), -1.0, {"health", "finance"}),
]
RECOVERY_DAYS = 5  # the dip fades gradually instead of snapping back


def wave_for(domain: str) -> list[float]:
    out = []
    for i, day in enumerate(dates):
        value = (
            math.sin(i / 6.0) * 0.5
            + math.sin(i / 40.0) * 0.3
            + random.uniform(-0.15, 0.15)
        )
        for start, end, shift, domains in PATCHES:
            if domain not in domains:
                continue
            if start <= day <= end:
                value += shift
            elif end < day <= end + timedelta(days=RECOVERY_DAYS):
                k = (day - end).days
                value += shift * (1 - k / (RECOVERY_DAYS + 1))
        out.append(value)
    return out


def scale(v: float, lo: float, hi: float) -> float:
    v = max(-1.5, min(1.5, v))
    return lo + (v + 1.5) / 3.0 * (hi - lo)


date_strs = [x.isoformat() for x in dates]

# HEALTH
wh = wave_for("health")
health = []
for i, ds in enumerate(date_strs):
    w = wh[i]
    health.append({
        "date": ds,
        "sleep_hours": round(scale(w, 5.5, 8.3) + random.uniform(-0.1, 0.1), 1),
        "steps": int(scale(w, 5000, 11500) + random.uniform(-200, 200)),
        "resting_heart_rate": int(scale(-w, 58, 68)),
        "active_minutes": int(scale(w, 20, 78)),
        "calories_burned": int(scale(w, 1800, 2460)),
        "stress_score": int(round(scale(-w, 18, 68))),
        "mood_score": int(round(scale(w, 50, 92))),
    })

# FINANCE
wf = wave_for("finance")
finance = []
balance = 6200.0
for i, ds in enumerate(date_strs):
    w = wf[i]
    daily_spend = round(scale(-w, 40, 130) + random.uniform(-5, 5), 2)
    income = 1200.0 if i % 15 == 0 else 0.0
    balance += income - daily_spend
    finance.append({
        "date": ds,
        "daily_spend": daily_spend,
        "account_balance": round(balance, 2),
        "savings_rate_pct": round(scale(w, 2, 24), 1),
        "credit_utilization_pct": round(scale(-w, 22, 78), 1),
        "financial_stress_score": int(round(scale(-w, 15, 75))),
    })

# PRODUCTIVITY
wp = wave_for("productivity")
productivity = []
for i, ds in enumerate(date_strs):
    w = wp[i]
    productivity.append({
        "date": ds,
        "focus_score": round(scale(w, 25, 95), 1),
        "deep_work_hours": round(scale(w, 0.5, 6.5), 1),
        "tasks_completed": int(scale(w, 2, 15)),
        "meetings_hours": round(random.uniform(1.0, 4.5), 1),
        "context_switches": int(scale(-w, 4, 24)),
        "burnout_risk_score": round(scale(-w, 8, 78), 1),
    })

os.makedirs("data", exist_ok=True)
for name, rows in (("health", health), ("finance", finance), ("productivity", productivity)):
    with open(f"data/{name}.json", "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)

print(f"Generated {n} days: {date_strs[0]} to {date_strs[-1]}")
print("Bad stretches (use these dates in your test questions):")
for start, end, shift, domains in PATCHES:
    print(f"  {start} to {end}: {', '.join(sorted(domains))}")