import os

FILES = {
"how_to_read_your_scores": """In this app, health scores work like this. Stress score runs from 0 to 100, and a weekly average above 50 counts as high stress. Mood score runs from 0 to 100, where higher is better. Sleep below about 6.5 hours a night and a resting heart rate above about 64 bpm are flagged. These thresholds are this app's own definitions, not clinical cut-offs.

In this app, finance scores work like this. Financial stress score runs from 0 to 100, and a weekly average above 50 counts as high. A savings rate below 10 percent is flagged as low, and credit utilization above 60 percent is flagged as high. These thresholds are this app's own alarm levels, not official credit or banking standards.

In this app, productivity scores work like this. Burnout risk score runs from 0 to 100, and a weekly average above 50 counts as high. Focus score runs from 0 to 100, and below 50 counts as low. Deep-work hours are the hours of uninterrupted, demanding work done in a day.
""",

"sleep_hygiene": """Many adults are advised to aim for roughly seven or more hours of sleep a night. In this app, a weekly average below about 6.5 hours is treated as poor sleep, and it often shows up alongside higher stress and lower mood in the same week.

Keeping a consistent bedtime and wake time, including on weekends, is one of the most commonly recommended ways to improve sleep. Regular timing often helps more than trying to catch up with one long sleep-in.

Reducing screen use and bright light in the hour before bed, avoiding caffeine late in the day, and keeping the bedroom cool and dark are common first steps for people whose sleep has slipped.
""",

"resting_heart_rate": """A typical resting heart rate for most adults is often quoted as 60 to 100 beats per minute, and fit people are frequently lower. Your own baseline matters more than the range, so a sustained rise above your usual level is the thing to notice.

In this app, a weekly average resting heart rate above about 64 bpm is flagged as elevated, because it tends to rise in the same weeks as poor sleep and high stress.

A resting heart rate that stays elevated for several weeks can reflect poor sleep, stress, illness, caffeine, dehydration or reduced fitness. If it stays high without an obvious cause, or comes with symptoms such as dizziness or chest discomfort, it is worth discussing with a doctor.
""",

"stress_management": """A stress score above 50 in this app means high stress. One high week is common. The pattern to watch is several high-stress weeks in a row, especially when sleep and mood are also dropping.

Short, regular practices such as a ten-minute walk, slow breathing exercises, or a brief pause between tasks are commonly suggested because they are easy to keep up during busy periods.

Stress tends to feed on itself: poor sleep raises stress, and high stress disrupts sleep. Improving one of the two, usually sleep, is a practical way to start easing both.
""",

"activity_and_mood": """Regular physical activity is widely associated with better mood, lower stress and better sleep. Public health guidance for adults commonly suggests around 150 minutes of moderate activity a week, though any increase helps.

In this app, weeks with fewer steps and fewer active minutes usually coincide with lower mood scores. Low activity is often a symptom of a hard week as well as a contributor to it.

On difficult days, a short walk is a realistic substitute for a full workout. Small, repeatable activity is easier to maintain than an ambitious plan that gets dropped.
""",

"when_to_see_a_doctor": """This is general information and not medical advice. Consider speaking with a doctor if high stress, poor sleep or an elevated resting heart rate persist for three or more weeks without improving.

Also consider it sooner if you notice symptoms such as chest pain, fainting, shortness of breath, persistent low mood, or feeling unable to cope. Seek urgent help for severe symptoms rather than waiting.

A routine check-up is a reasonable step when several health indicators worsen at the same time, even if each one alone seems minor. Bring your recent sleep, activity and stress trends to the appointment.
""",

"savings_rate": """Savings rate is the share of income you set aside. A common rule of thumb is to aim for around 10 to 20 percent, though the right figure depends on your situation. In this app, a weekly savings rate below 10 percent is flagged as low.

A falling savings rate over several weeks usually means spending is rising or income is flat. Looking at which categories grew can show whether the change is temporary or a new habit.

Automating a transfer to savings on payday makes saving the default. Even a small automatic amount protects the habit during expensive months.
""",

"credit_utilization": """Credit utilization is the share of your available credit that you are using. Credit guidance commonly recommends keeping it under about 30 percent. This app uses a stricter alarm level and flags a weekly average above 60 percent as high.

Rising utilization often means everyday expenses are being covered by borrowing. When it climbs together with a falling savings rate, it is an early sign of financial strain.

Paying down the highest-interest balances first, and paying more than the minimum when possible, is a common way to bring utilization back down.
""",

"emotional_spending": """Emotional spending is buying driven by mood, stress or boredom rather than need. Many people spend more on takeout, shopping and convenience during stressful weeks.

In this app, daily spending tends to rise in the same weeks that stress and burnout risk rise. Comparing your high-stress weeks with your high-spending weeks can reveal the link.

A short waiting period before non-essential purchases, such as 24 hours, and a small fixed budget for treats are common ways to reduce impulse spending without cutting it out.
""",

"budgeting_basics": """A simple budget splits income into needs, wants and savings. A common starting split is 50 percent needs, 30 percent wants and 20 percent savings, adjusted to fit your own costs.

Reviewing spending weekly rather than monthly catches problems earlier. Looking at the last seven days takes only a few minutes and shows trends before they become habits.

Keeping a small emergency fund, often suggested at three to six months of essential expenses, reduces the need to borrow when an unexpected cost arrives.
""",

"when_to_see_a_financial_planner": """This is general information and not financial advice. Consider a financial planner when your savings rate has stayed low and credit utilization has stayed high for several weeks in a row.

A planner can also help with big decisions such as consolidating debt, building an emergency fund, planning for a major purchase, or setting retirement contributions.

Before a first meeting, gather recent statements, a list of debts with interest rates, and your monthly income and spending. Check that the planner is qualified and how they are paid.
""",

"burnout_signs": """Burnout is prolonged exhaustion from sustained pressure, often with reduced effectiveness and growing detachment from work. In this app, a burnout risk score above 50 is considered high.

Early signs include falling deep-work hours, more context switching, lower focus scores and poorer sleep at the same time. Rising burnout risk with falling deep work often comes before a larger productivity drop.

Burnout builds over weeks, so catching it early matters. Acting on the first two or three weeks of decline is much easier than recovering after a long slide.
""",

"deep_work": """Deep work is focused, uninterrupted effort on a demanding task. Many people find two or three protected blocks of one to two hours a day more productive than a full day of fragmented time.

In this app, deep-work hours and focus scores drop in the same weeks that sleep is poor. Low focus during a bad-sleep week is usually a symptom rather than a separate problem.

Scheduling focus blocks in your best hours, silencing notifications during them, and keeping a short list of priorities are common ways to protect deep work.
""",

"meetings_and_context_switching": """Heavy meeting loads and frequent task switching fragment attention. Each switch carries a recovery cost, so many short interruptions can cost more than their length suggests.

A high number of context switches alongside low deep-work hours usually points to a schedule problem rather than a motivation problem.

Batching meetings into fixed windows, declining meetings without a clear purpose, and checking messages at set times rather than continuously can free up focus time.
""",

"recovery_after_burnout": """Recovering from burnout usually starts with reducing load rather than working harder. Protecting sleep, taking real breaks and lowering commitments for a few weeks are the common first steps.

Recovery is gradual. Expect focus and energy to return over weeks, and rebuild deep-work time in small steps rather than returning to full intensity at once.

If exhaustion, low mood or loss of motivation persist despite rest, speaking with a doctor or counsellor is sensible.
""",

"stress_money_sleep_connection": """Sleep, stress, money and focus influence each other. A bad week in one area often shows up in the others.

Money worry can raise stress and disrupt sleep, while poor sleep and high stress can increase spending and reduce focus. When several indicators worsen together, look for the common cause, such as a deadline, an unexpected expense or an illness, rather than treating each one separately.

The most effective single lever is usually sleep, because improving it tends to lower stress, steady spending and restore focus together.
""",
}

os.makedirs("data/knowledge", exist_ok=True)
for name, text in FILES.items():
    with open(f"data/knowledge/{name}.txt", "w", encoding="utf-8") as f:
        f.write(text.strip() + "\n")

print(f"Wrote {len(FILES)} files to data/knowledge/")