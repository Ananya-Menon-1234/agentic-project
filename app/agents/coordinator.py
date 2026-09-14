import json
from datetime import datetime

from dotenv import load_dotenv
from langchain_groq import ChatGroq

from app.graph.state import AgentState

load_dotenv()

llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0)

ROUTER_PROMPT = """You are a routing classifier. Given a user's question, decide \
which domains are relevant: health, finance, productivity. A question can match \
more than one domain. If the question is a general "how am I doing overall" type \
question with no clear domain, return all three.

Respond with ONLY a JSON array of the relevant domain names, nothing else. \
Only 3 values are accepted: "health", "finance", "productivity" Examples:

Question: "How's my sleep been?"
Answer: ["health"]

Question: "Am I overworking myself?"
Answer: ["productivity"]

Question: "Should I be worried about my spending and my stress levels?"
Answer: ["finance", "health"]

Question: "How am I doing overall?"
Answer: ["health", "finance", "productivity"]

Question: "{query}"
Answer:"""


async def coordinator_node(state: AgentState) -> dict:
    query = state["query"]

    result = await llm.ainvoke(ROUTER_PROMPT.format(query=query))
    raw = result.content.strip()

    try:
        domains = json.loads(raw)
        domains = [d for d in domains if d in ("health", "finance", "productivity")]
        if not domains:
            raise ValueError("empty or invalid domain list")
    except (json.JSONDecodeError, ValueError):
        domains = ["health", "finance", "productivity"]

    print(f"\n{'='*70}")
    print(f"[coordinator] {datetime.now().isoformat()}")
    print(f"  query: {query}")
    print(f"  routing to: {domains}")
    print(f"{'='*70}\n")
    return {"relevant_domains": domains}
