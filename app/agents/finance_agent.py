from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent
import os

load_dotenv()

llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0)


mcp_client = MultiServerMCPClient(
    {
        "finance": {
            "transport": "http",
            "url": os.environ.get("FINANCE_MCP_URL", "http://127.0.0.1:8001/mcp"),
        }
    }
)

FINANCE_SYSTEM_PROMPT = (
    "You are the finance agent. You have three tools:\n"
    "- get_finance_data(days): raw daily records, for questions about specific recent days\n"
    "- get_finance_stats(days): averages/min/max plus latest balance, for 'how have my finances been' or 'overall summary' questions\n"
    "- compare_finance_trend(days): first-half vs second-half comparison, for 'has it improved' or 'beginning vs end' questions\n\n"
    "Convert timeframes in the question to a days value: 'this week'=7, "
    "'past two weeks'=14, 'this month' or 'overall'=30. If no timeframe is "
    "mentioned, default to 30 for stats/comparison questions, or 7 for "
    "general check-ins.\n\n"
    "Call the appropriate tool, then respond with a short 3-4 sentence "
    "verdict citing concrete numbers (spend, savings rate, credit "
    "utilization). No tables, no markdown headers, no emoji."
)


async def create_finance_agent():
    tools = await mcp_client.get_tools()

    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=FINANCE_SYSTEM_PROMPT,
    )

    return agent