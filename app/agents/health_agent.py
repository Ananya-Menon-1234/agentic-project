from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
import os

load_dotenv()


llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0)


mcp_client = MultiServerMCPClient({
    "health": {
        "transport": "http",
        "url": os.environ.get("HEALTH_MCP_URL", "http://127.0.0.1:8000/mcp"),
    }
})

HEALTH_SYSTEM_PROMPT = (
    "You are the health agent. You have three tools:\n"
    "- get_health_data(days): raw daily records, for questions about specific recent days\n"
    "- get_health_stats(days): averages/min/max over a period, for 'how has my health been' or 'overall summary' questions\n"
    "- compare_health_trend(days): first-half vs second-half comparison, for 'has it improved' or 'beginning vs end' questions\n\n"
    "Convert timeframes in the question to a days value: 'this week'=7, "
    "'past two weeks'=14, 'this month' or 'overall'=30. If no timeframe is "
    "mentioned, default to 30 (the full month) for stats/comparison questions, "
    "or 7 for general check-ins.\n\n"
    "Call the appropriate tool, then respond with a short 3-4 sentence "
    "verdict citing concrete numbers. No tables, no markdown headers, no emoji."
)


async def create_health_agent():

    tools = await mcp_client.get_tools()

    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=HEALTH_SYSTEM_PROMPT
    )

    return agent