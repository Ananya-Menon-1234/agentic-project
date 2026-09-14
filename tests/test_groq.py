from app.llm.groq import llm


response = llm.invoke(
    "what is aldi's?"
)

print(response.content)