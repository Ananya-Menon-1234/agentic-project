import asyncio

from app.agents.health_agent import create_health_agent


async def main():

    agent = await create_health_agent()

    response = await agent.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "Get my health data."
                }
            ]
        }
    )

    print("\n--- AGENT RESPONSE ---\n")

    for message in response["messages"]:
        print(message)


if __name__ == "__main__":
    asyncio.run(main())