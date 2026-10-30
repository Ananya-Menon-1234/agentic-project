from enum import Enum

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field

from app.graph.state import AgentState

load_dotenv()

llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0)


class ActionType(str, Enum):
    none = "none"
    doctor = "doctor"
    financial_planner = "financial_planner"
    both = "both"


class InsightResult(BaseModel):
    summary: str = Field(
        description="2-5 sentence plain-text summary covering only the domains that were reported."
    )
    action: ActionType = Field(
        description="Which professional to schedule, based on severity of the findings."
    )
    reasoning: str = Field(description="One sentence on why this action was chosen.")


structured_llm = llm.with_structured_output(InsightResult, method="json_schema")

INSIGHT_PROMPT = """You are the Insight Agent. Summarize the reports below in 2-5 plain-text \
sentences, covering only the domains that were reported.

Then choose an action:
- "doctor": the HEALTH report shows sustained or severe concern (severity 6/10 or higher, \
or clearly worsening stress, sleep, or resting heart rate)
- "financial_planner": the FINANCE report shows sustained or severe concern (severity 6/10 \
or higher, or low savings rate with high credit utilization)
- "both": both of the above apply
- "none": findings are normal or only mildly concerning

Only choose an action for a domain that has a report below.

{reports}

RETRIEVED CONTEXT (background only; base the action on the reports above, not on this):
{context}
"""

DOMAIN_KEYS = [
    ("health", "health_report", "HEALTH REPORT"),
    ("finance", "finance_report", "FINANCE REPORT"),
    ("productivity", "productivity_report", "PRODUCTIVITY REPORT"),
]


def _apply_guardrails(action: ActionType, domains: list[str]) -> str:
    """Never act on a domain that wasn't actually analyzed this run."""
    wants_doctor = action in (ActionType.doctor, ActionType.both) and "health" in domains
    wants_planner = action in (ActionType.financial_planner, ActionType.both) and "finance" in domains

    if wants_doctor and wants_planner:
        return "both"
    if wants_doctor:
        return "doctor"
    if wants_planner:
        return "financial_planner"
    return "none"


async def insight_node(state: AgentState) -> dict:
    sections = [
        f"{label}:\n{state[key]}"
        for _, key, label in DOMAIN_KEYS
        if state.get(key)
    ]
    if not sections:
        print("[insight] no domain reports available; skipping LLM call")
        return {
            "insight": "No domain reports were produced for this question, so I can't summarize it.",
            "action_decision": "none",
        }
    prompt = INSIGHT_PROMPT.format(
        reports="\n\n".join(sections),
        context=state.get("retrieved_context") or "None",
    )

    try:
        result: InsightResult = await structured_llm.ainvoke(prompt)
    except Exception as e:
        print(f"[insight] structured output failed ({e}); defaulting to no action")
        return {
            "insight": "Could not generate a full summary this time.",
            "action_decision": "none",
        }

    domains = state.get("relevant_domains", [])
    decision = _apply_guardrails(result.action, domains)

    print(f"\n{'='*70}")
    print(f"[insight] model_action={result.action.value} -> final_action={decision}")
    print(f"[insight] reasoning: {result.reasoning}")
    print(f"{'='*70}\n")

    return {"insight": result.summary, "action_decision": decision}


def route_after_insight(state: AgentState) -> str:
    return "end" if state.get("action_decision", "none") == "none" else "action"