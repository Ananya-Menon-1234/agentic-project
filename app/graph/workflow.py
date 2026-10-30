from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from app.agents.action_agent import action_node
from app.agents.coordinator import coordinator_node
from app.agents.finance_agent import create_finance_agent
from app.agents.health_agent import create_health_agent
from app.agents.insight_agent import insight_node, route_after_insight
from app.agents.productivity_agent import create_productivity_agent
from app.agents.retrieval_agent import retrieval_node
from app.graph.state import AgentState

_fallback_llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0)


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
def _log_state(node_name: str, state: dict, direction: str) -> None:
    print(f"\n{'=' * 70}")
    print(f"[{node_name}] {direction}")
    print(f"{'=' * 70}")
    for key, value in state.items():
        preview = str(value)
        if len(preview) > 200:
            preview = preview[:200] + "... (truncated)"
        print(f"  {key}: {preview}")
    print(f"{'=' * 70}\n")


# ---------------------------------------------------------------------------
# Helpers for reading an agent's result
# ---------------------------------------------------------------------------
def _text(content) -> str:
    """Message content can be a string or a list of blocks; return plain text."""
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        return "".join(
            b.get("text", "") if isinstance(b, dict) else str(b) for b in content
        ).strip()
    return ""


def _final_report(result: dict) -> str:
    """Last non-empty AI message that is not just announcing a tool call."""
    for m in reversed(result["messages"]):
        if m.type == "ai" and not getattr(m, "tool_calls", None):
            text = _text(m.content)
            if text:
                return text
    return ""


def _last_tool_output(result: dict) -> str:
    for m in reversed(result["messages"]):
        if m.type == "tool":
            return _text(m.content)
    return ""


async def _report_or_fallback(domain: str, result: dict) -> str:
    """Use the agent's report; if it is empty, summarize the tool output directly."""
    report = _final_report(result)
    if report:
        return report

    tool_out = _last_tool_output(result)
    if not tool_out:
        return ""

    print(f"[{domain}] agent returned empty text; summarizing tool output directly")
    try:
        resp = await _fallback_llm.ainvoke(
            f"In 3-4 plain sentences, summarize these {domain} stats and say what "
            f"looks healthy or concerning, with a severity from 1-10 if concerning:\n{tool_out}"
        )
        text = _text(resp.content)
        if text:
            return text
    except Exception as e:
        print(f"[{domain}] fallback summary failed: {e}")

    # Last resort: pass the raw numbers on so the insight agent still has data.
    return f"Raw {domain} stats (no summary available): {tool_out}"


# ---------------------------------------------------------------------------
# Domain nodes (one shared implementation)
# ---------------------------------------------------------------------------
async def _run_domain(domain: str, create_agent, state_key: str, state: AgentState) -> dict:
    _log_state(domain, state, "IN")
    agent = await create_agent()
    msgs = {"messages": [{"role": "user", "content": state["query"]}]}

    result = await agent.ainvoke(msgs)
    report = _final_report(result)
    if not report:
        print(f"[{domain}] empty report, retrying once")
        result = await agent.ainvoke(msgs)
        report = await _report_or_fallback(domain, result)

    output = {state_key: report}
    _log_state(domain, output, "OUT (added to shared state)")
    return output


async def health_node(state: AgentState) -> dict:
    return await _run_domain("health", create_health_agent, "health_report", state)


async def finance_node(state: AgentState) -> dict:
    return await _run_domain("finance", create_finance_agent, "finance_report", state)


async def productivity_node(state: AgentState) -> dict:
    return await _run_domain(
        "productivity", create_productivity_agent, "productivity_report", state
    )


# ---------------------------------------------------------------------------
# Per-question reset and routing
# ---------------------------------------------------------------------------
def reset_query_state(state: AgentState) -> dict:
    """Clear results left over from the previous question on the same thread."""
    return {
        "health_report": "",
        "finance_report": "",
        "productivity_report": "",
        "insight": "",
        "action_decision": "none",
        "action_taken": "none",
        "retrieved_context": "",
        "retrieval_sources": [],
    }


def route_from_coordinator(state: AgentState) -> list[str]:
    return state["relevant_domains"]


# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------
def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("reset", reset_query_state)
    graph.add_node("coordinator", coordinator_node)
    graph.add_node("health", health_node)
    graph.add_node("finance", finance_node)
    graph.add_node("productivity", productivity_node)
    graph.add_node("retrieval", retrieval_node)
    graph.add_node("insight", insight_node)
    graph.add_node("action", action_node)

    graph.add_edge(START, "reset")
    graph.add_edge("reset", "coordinator")

    # Fan out only to the domains the coordinator selected
    graph.add_conditional_edges(
        "coordinator",
        route_from_coordinator,
        ["health", "finance", "productivity"],
    )

    # Separate edges, not a wait-for-all join: the coordinator may route only
    graph.add_edge("health", "retrieval")
    graph.add_edge("finance", "retrieval")
    graph.add_edge("productivity", "retrieval")
    graph.add_edge("retrieval", "insight")

    graph.add_conditional_edges(
        "insight", route_after_insight, {"action": "action", "end": END}
    )
    graph.add_edge("action", END)

    checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)