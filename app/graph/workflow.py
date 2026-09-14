import json

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from app.graph.state import AgentState
from app.agents.coordinator import coordinator_node
from app.agents.health_agent import create_health_agent
from app.agents.finance_agent import create_finance_agent
from app.agents.productivity_agent import create_productivity_agent
from app.agents.insight_agent import insight_node, route_after_insight
from app.agents.action_agent import action_node


def _log_state(node_name: str, state: dict, direction: str) -> None:
    print(f"\n{'='*70}")
    print(f"[{node_name}] {direction}")
    print(f"{'='*70}")
    for key, value in state.items():
        preview = str(value)
        if len(preview) > 200:
            preview = preview[:200] + "... (truncated)"
        print(f"  {key}: {preview}")
    print(f"{'='*70}\n")


async def health_node(state: AgentState) -> dict:
    _log_state("health", state, "IN")
    agent = await create_health_agent()
    result = await agent.ainvoke({"messages": [{"role": "user", "content": state["query"]}]})
    output = {"health_report": result["messages"][-1].content}
    _log_state("health", output, "OUT (added to shared state)")
    return output


async def finance_node(state: AgentState) -> dict:
    _log_state("finance", state, "IN")
    agent = await create_finance_agent()
    result = await agent.ainvoke({"messages": [{"role": "user", "content": state["query"]}]})
    output = {"finance_report": result["messages"][-1].content}
    _log_state("finance", output, "OUT (added to shared state)")
    return output


async def productivity_node(state: AgentState) -> dict:
    _log_state("productivity", state, "IN")
    agent = await create_productivity_agent()
    result = await agent.ainvoke({"messages": [{"role": "user", "content": state["query"]}]})
    output = {"productivity_report": result["messages"][-1].content}
    _log_state("productivity", output, "OUT (added to shared state)")
    return output


def route_from_coordinator(state: AgentState) -> list[str]:
    return state["relevant_domains"]


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("coordinator", coordinator_node)
    graph.add_node("health", health_node)
    graph.add_node("finance", finance_node)
    graph.add_node("productivity", productivity_node)
    graph.add_node("insight", insight_node)
    graph.add_node("action", action_node)

    graph.add_edge(START, "coordinator")

    graph.add_conditional_edges(
        "coordinator",
        route_from_coordinator,
        ["health", "finance", "productivity"],
    )

    graph.add_edge("health", "insight")
    graph.add_edge("finance", "insight")
    graph.add_edge("productivity", "insight")

    graph.add_conditional_edges(
        "insight", route_after_insight, {"action": "action", "end": END}
    )
    graph.add_edge("action", END)

    checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)