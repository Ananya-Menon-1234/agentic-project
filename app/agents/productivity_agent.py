from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
import os

load_dotenv()

llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0)

mcp_client = MultiServerMCPClient(
    {
        "productivity": {
            "transport": "http",
            "url": os.environ.get("PRODUCTIVITY_MCP_URL", "http://127.0.0.1:8002/mcp"),
        }
    }
)

PRODUCTIVITY_SYSTEM_PROMPT = (
    "You are the productivity agent. You have these tools:\n"
    "- get_productivity_data(days, start_date, end_date): raw daily records\n"
    "- get_productivity_stats(days, start_date, end_date): averages/min/max of each metric\n"
    "- compare_productivity_trend(days, start_date, end_date): first half vs second half of one period\n"
    "- compare_productivity_periods(start_a, end_a, start_b, end_b): two separate periods, e.g. April vs July\n\n"
    "The data covers 2026-04-01 to 2026-10-25. For a named month, call get_productivity_stats "
    "with start_date and end_date, for example July = 2026-07-01 to 2026-07-31. To compare "
    "two months, call compare_productivity_periods. Use `days` only for relative windows: "
    "'this week'=7, 'past two weeks'=14, 'this month' or 'recently'=30. If no timeframe is "
    "given, use days=30. If a tool returns an error, say so and mention the available range.\n\n"
    "After calling a tool, respond with a short 3-4 sentence verdict citing concrete numbers "
    "(focus score, deep-work hours, burnout risk). No tables, no markdown headers, no emoji."
)


async def create_productivity_agent():
    tools = await mcp_client.get_tools()

    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=PRODUCTIVITY_SYSTEM_PROMPT,
    )

    return agent