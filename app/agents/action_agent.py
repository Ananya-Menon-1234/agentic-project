from app.graph.state import AgentState
from app.mcp.reminder_client import schedule_reminder

async def action_node(state: AgentState) -> dict:
    text = state["insight"].lower()
    results = []

    if "action: doctor" in text or "action: both" in text:
        r = schedule_reminder(
            summary="General health checkup",
            description=(
                "Your personal insight agent flagged concerning health trends "
                "over the past period. This is a reminder to book a checkup "
                "with a doctor. Review your latest health report before going."
            ),
            days_from_now=3,
        )
        results.append(f"Doctor checkup reminder: {r['status']} for {r['scheduled_for']}")

    if "action: financial_planner" in text or "action: both" in text:
        r = schedule_reminder(
            summary="Meeting with financial planner",
            description=(
                "Your personal insight agent flagged concerning financial trends "
                "over the past period. This is a reminder to set up time with a "
                "financial planner. Review your latest finance report first."
            ),
            days_from_now=5,
        )
        results.append(f"Financial planner reminder: {r['status']} for {r['scheduled_for']}")

    return {"action_taken": "\n".join(results) if results else "none"}