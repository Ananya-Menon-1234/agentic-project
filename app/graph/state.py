from typing import TypedDict


class AgentState(TypedDict, total=False):
    query: str
    relevant_domains: list[str]
    health_report: str
    finance_report: str
    productivity_report: str
    insight: str
    action_decision: str
    action_taken: str
    retrieved_context: str
    retrieval_sources: list[str]