from dotenv import load_dotenv
from langchain_groq import ChatGroq

from app.agents.coordinator import AgentState

load_dotenv()

llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0)

INSIGHT_PROMPT_TEMPLATE = """You are the Insight Agent. Combine these three domain \
reports into one short overall summary (5-6 sentences, plain text, no markdown). \
Then, on a final line by itself, output exactly one of:
ACTION: none
ACTION: doctor
ACTION: financial_planner
ACTION: both

HEALTH REPORT:
{health_report}

FINANCE REPORT:
{finance_report}

PRODUCTIVITY REPORT:
{productivity_report}
"""


async def insight_node(state: AgentState) -> dict:
    prompt = INSIGHT_PROMPT_TEMPLATE.format(
        health_report=state.get("health_report", "N/A"),
        finance_report=state.get("finance_report", "N/A"),
        productivity_report=state.get("productivity_report", "N/A"),
    )
    result = await llm.ainvoke(prompt)
    print(f"\n{'='*70}")
    print(f"[insight] received reports, generated:")
    print(f"  {result.content[:300]}...")
    print(f"{'='*70}\n")
    return {"insight": result.content}


def route_after_insight(state: AgentState) -> str:
    """Conditional edge function — tells the graph whether to go to
    the action node or straight to END."""
    text = state["insight"].lower()
    if "action: none" in text:
        return "end"
    if "action: doctor" in text or "action: financial_planner" in text or "action: both" in text:
        return "action"
    return "end"