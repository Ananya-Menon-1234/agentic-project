import re
from typing import Literal

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field

from app.graph.state import AgentState
from app.rag.ingest import ensure_indexed

load_dotenv()

llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0)


class RouteDecision(BaseModel):
    sources: list[Literal["journal", "knowledge"]] = Field(
        description="Which sources to search. Empty list if neither adds value."
    )
    search_query: str = Field(
        description="Short natural-language query for semantic search."
    )
    month: str = Field(
        default="",
        description="YYYY-MM if the question is about one specific month of 2026, else empty string.",
    )
    reasoning: str = Field(description="One sentence on why these sources were chosen.")


# json_schema asks Groq for JSON matching the schema, instead of a fake tool call
# whose name the model sometimes mangles.
router_llm = llm.with_structured_output(RouteDecision, method="json_schema")

ROUTER_PROMPT = """You route questions to text sources. Numbers (averages, scores, balances) \
come from other tools, so never search for them. Choose any of:
- "journal": the user's own diary entries about what was happening in their life \
(Apr-Oct 2026). Use for WHY something happened, what was going on during a period, \
or what caused a bad stretch.
- "knowledge": general written guidance. Use for what a score or metric means, what is \
normal, warning signs, or what to do about something.
Return an empty list if neither adds anything, for example a greeting or a request that \
only needs exact numbers ("average sleep in July", "my balance").

Also write search_query: a short natural-language query (no JSON, no tool names).
If the question is about one specific month, set month to YYYY-MM (July 2026 = "2026-07"); \
otherwise leave it empty.

Question: {query}
Domains being analyzed: {domains}
"""

MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
}


def _guess_month(query: str) -> str:
    """Deterministic fallback: a month is used only if exactly one is named."""
    q = query.lower()
    found = [n for name, n in MONTHS.items() if re.search(rf"\b{name}\b", q)]
    return f"2026-{found[0]:02d}" if len(found) == 1 else ""


async def _route(query: str, domains: list[str]) -> RouteDecision:
    prompt = ROUTER_PROMPT.format(query=query, domains=", ".join(domains) or "all")
    last_err = None
    for attempt in (1, 2):
        try:
            return await router_llm.ainvoke(prompt)
        except Exception as e:
            last_err = e
            print(f"[retrieval] router attempt {attempt} failed: {str(e)[:160]}")
    raise last_err


def _search(collection, query: str, k: int, where=None) -> list[str]:
    n = collection.count()
    if n == 0:
        return []
    res = collection.query(query_texts=[query], n_results=min(k, n), where=where)
    return res["documents"][0]


def _journal_where(domains: list[str], month: str):
    conditions = []
    if domains:
        # 'general' entries span several domains, so they always qualify
        conditions.append({"domain": {"$in": list(domains) + ["general"]}})
    if month:
        conditions.append({"month": month})
    if not conditions:
        return None
    return conditions[0] if len(conditions) == 1 else {"$and": conditions}


async def retrieval_node(state: AgentState) -> dict:
    query = state["query"]
    domains = state.get("relevant_domains", [])
    journal, knowledge = ensure_indexed()

    try:
        decision = await _route(query, domains)
        sources, search_query = decision.sources, decision.search_query
        month = decision.month if re.fullmatch(r"\d{4}-\d{2}", decision.month or "") else ""
        print(
            f"[retrieval] sources={sources} query='{search_query}' month='{month}' "
            f"| {decision.reasoning}"
        )
    except Exception:
        sources, search_query, month = ["journal", "knowledge"], query, _guess_month(query)
        print(f"[retrieval] router failed twice; fallback: both sources, month='{month}'")

    blocks = []
    if "journal" in sources:
        docs = _search(journal, search_query, 3, _journal_where(domains, month))
        if not docs and month:  # month filter matched nothing; retry without it
            docs = _search(journal, search_query, 3, _journal_where(domains, ""))
        blocks.append(("YOUR JOURNAL", docs))
    if "knowledge" in sources:
        blocks.append(("GUIDANCE", _search(knowledge, search_query, 2)))

    context = "\n\n".join(
        f"{title}:\n" + "\n".join(f"- {d}" for d in docs)
        for title, docs in blocks if docs
    )
    print(f"[retrieval] retrieved {sum(len(d) for _, d in blocks)} chunks")
    return {"retrieved_context": context, "retrieval_sources": sources}