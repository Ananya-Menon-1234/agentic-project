import json
import math
import random
from datetime import date, timedelta

random.seed(42)

START = date(2026, 9, 1)
END = date(2026, 9, 30)

dates = []
d = START
while d <= END:
    dates.append(d)
    d += timedelta(days=1)

n = len(dates)
date_strs = [d.isoformat() for d in dates]


wave = []
for i in range(n):
    cycle = math.sin(i / 6.0) * 0.5
    noise = random.uniform(-0.15, 0.15)
    value = cycle + noise

    if 9 <= i <= 17:
        value -= 1.1
    elif 18 <= i <= 23:
        value += (i - 17) * 0.15

    wave.append(value)


def scale(v, lo, hi):
    v = max(-1.5, min(1.5, v))
    return lo + (v + 1.5) / 3.0 * (hi - lo)


# HEALTH
health = []
for i, ds in enumerate(date_strs):
    w = wave[i]
    health.append({
        "date": ds,
        "sleep_hours": round(scale(w, 5.5, 8.3) + random.uniform(-0.1, 0.1), 1),
        "steps": int(scale(w, 5000, 11500) + random.uniform(-200, 200)),
        "resting_heart_rate": int(scale(-w, 58, 68)),
        "active_minutes": int(scale(w, 20, 78)),
        "calories_burned": int(scale(w, 1800, 2460)),
        "stress_score": round(scale(-w, 18, 68), 0),
        "mood_score": round(scale(w, 50, 92), 0),
    })

# FINANCE
finance = []
balance = 6200.0
for i, ds in enumerate(date_strs):
    w = wave[i]
    daily_spend = round(scale(-w, 40, 130) + random.uniform(-5, 5), 2)
    income = 1500.0 if i % 15 == 0 else 0.0
    balance += income - daily_spend
    finance.append({
        "date": ds,
        "daily_spend": daily_spend,
        "account_balance": round(balance, 2),
        "savings_rate_pct": round(scale(w, 2, 24), 1),
        "credit_utilization_pct": round(scale(-w, 22, 78), 1),
        "financial_stress_score": round(scale(-w, 15, 75), 0),
    })

# PRODUCTIVITY
productivity = []
for i, ds in enumerate(date_strs):
    w = wave[i]
    productivity.append({
        "date": ds,
        "focus_score": round(scale(w, 25, 95), 1),
        "deep_work_hours": round(scale(w, 0.5, 6.5), 1),
        "tasks_completed": int(scale(w, 2, 15)),
        "meetings_hours": round(random.uniform(1.0, 4.5), 1),
        "context_switches": int(scale(-w, 4, 24)),
        "burnout_risk_score": round(scale(-w, 8, 78), 1),
    })

with open("data/health.json", "w") as f:
    json.dump(health, f, indent=2)
with open("data/finance.json", "w") as f:
    json.dump(finance, f, indent=2)
with open("data/productivity.json", "w") as f:
    json.dump(productivity, f, indent=2)

print(f"Generated {n} days ({date_strs[0]} to {date_strs[-1]})")
print("Wrote: data/health.json, data/finance.json, data/productivity.json")
print(f"Rough patch (should trigger ACTION): {date_strs[9]} to {date_strs[17]}")