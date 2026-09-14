import asyncio

import gradio as gr

from app.graph.workflow import build_graph

_graph = None 


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


async def _run_query(query: str, thread_id: str) -> tuple[str, str, str, str, str]:
    app = get_graph()
    config = {"configurable": {"thread_id": thread_id or "default-user"}}

    result = await app.ainvoke({"query": query}, config=config)

    health = result.get("health_report", "_(not requested)_")
    finance = result.get("finance_report", "_(not requested)_")
    productivity = result.get("productivity_report", "_(not requested)_")
    insight = result.get("insight", "_(no insight generated)_")
    action = result.get("action_taken", "none")

    return health, finance, productivity, insight, action


def run_query_sync(query: str, thread_id: str):
    if not query or not query.strip():
        empty = "_(ask a question above)_"
        return empty, empty, empty, empty, "none"
    return asyncio.run(_run_query(query, thread_id))


EXAMPLE_QUESTIONS = [
    "How am I doing overall this week?",
    "How has my productivity been this month?",
    "Overall, has my health improved from the beginning to the end of the month?",
    "My stress and financial stress scores seem high this month — should I see a doctor or a financial planner?",
]

with gr.Blocks(title="Personal Insight Agent") as demo:
    gr.Markdown(
        "# Personal Insight Agent\n"
        "Ask about your health, finances, or productivity. "
        "A coordinator routes your question to the right specialist agent(s), "
        "and an insight agent may schedule a reminder if something looks concerning."
    )

    with gr.Row():
        query_box = gr.Textbox(
            label="Your question",
            placeholder="e.g. How has my productivity been this month?",
            lines=2,
        )
        thread_box = gr.Textbox(
            label="Thread ID (memory key)",
            value="default-user",
            scale=0,
        )

    submit_btn = gr.Button("Ask", variant="primary")

    gr.Examples(examples=EXAMPLE_QUESTIONS, inputs=query_box)

    with gr.Row():
        health_out = gr.Textbox(label="Health report", lines=4)
        finance_out = gr.Textbox(label="Finance report", lines=4)
        productivity_out = gr.Textbox(label="Productivity report", lines=4)

    insight_out = gr.Textbox(label="Insight (overall summary)", lines=4)
    action_out = gr.Textbox(label="Action taken", lines=2)

    submit_btn.click(
        fn=run_query_sync,
        inputs=[query_box, thread_box],
        outputs=[health_out, finance_out, productivity_out, insight_out, action_out],
    )
    query_box.submit(
        fn=run_query_sync,
        inputs=[query_box, thread_box],
        outputs=[health_out, finance_out, productivity_out, insight_out, action_out],
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, share=True)