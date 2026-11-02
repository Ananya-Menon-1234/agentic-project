# Personal Insight Agent

A multi-agent AI system that analyzes synthetic **health, finance, and productivity data**, retrieves supporting context from a vector database, and generates cross-domain insights using specialized AI agents.

The project was built to explore the engineering behind an agentic AI application, including **agent orchestration, state management, MCP-based tool access, agentic RAG, validated structured outputs, action execution, observability, containerization, and cloud deployment**.

> **Note:** All health, financial, and productivity data, and all journal and guidance text, used in this project is synthetic and written for demonstration purposes. It is not intended for real medical, financial, or productivity recommendations.

---

## Overview

Personal data is often spread across different sources. A health application may contain sleep and activity information, a financial application may contain spending information, and productivity tools may contain information about focus and workload.

This project explores whether a multi-agent system can bring these domains together and provide a higher-level view.

Instead of using one large agent for everything, the system uses specialized agents:

* **Coordinator Agent**: determines which domains are relevant to a user's question
* **Health Agent**: analyzes health-related data through MCP tools
* **Finance Agent**: analyzes financial data through MCP tools
* **Productivity Agent**: analyzes productivity data through MCP tools
* **Retrieval Agent**: decides which text knowledge source to search (if any) and retrieves relevant context
* **Insight Agent**: combines the domain reports and retrieved context, and produces a validated action decision
* **Action Agent**: executes the selected action

The overall workflow is:

```text
                         User
                           │
                           ▼
                  ┌─────────────────┐
                  │ Reset state     │
                  └────────┬────────┘
                           ▼
                  ┌─────────────────┐
                  │ Coordinator     │
                  │ Agent           │
                  └────────┬────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────────┐
        │  Health  │ │ Finance  │ │ Productivity │
        │  Agent   │ │  Agent   │ │    Agent     │
        └────┬─────┘ └────┬─────┘ └──────┬───────┘
             ▼            ▼              ▼
        Health MCP   Finance MCP   Productivity MCP
             ▼            ▼              ▼
        health.json  finance.json  productivity.json
             │            │              │
             └────────────┼──────────────┘
                          ▼
                 ┌─────────────────┐       ┌──────────────────────┐
                 │ Retrieval Agent │──────▶│ ChromaDB             │
                 │ (router LLM)    │       │  • journal           │
                 └────────┬────────┘       │  • knowledge_base    │
                          │                └──────────────────────┘
                          ▼
                 ┌─────────────────┐
                 │ Insight Agent   │
                 │ (validated      │
                 │  action decision)│
                 └────────┬────────┘
                          │
                  action needed?
                    │         │
                   yes        no
                    ▼         ▼
            ┌────────────┐   END
            │ Action     │
            │ Agent      │
            └─────┬──────┘
                  ▼
                 END
```

---

## Key Features

### Dynamic Agent Routing

The Coordinator Agent classifies the user's question and runs only the domain agents that are relevant.

```text
"How has my productivity been this month?"
                │
                ▼
        Coordinator Agent
                │
                ▼
       Productivity Agent
```

Whereas:

```text
"How am I doing overall across my health,
 finances and productivity?"
                │
                ▼
        Coordinator Agent
                │
       ┌────────┼────────┐
       ▼        ▼        ▼
    Health   Finance  Productivity
```

This prevents unnecessary agents (and LLM calls) from running for every query.

### Date-Aware MCP Tools

Each domain's MCP server exposes tools that accept either a relative window (`days`) or an explicit date range (`start_date`, `end_date`), plus a tool for comparing two separate periods. This lets the system answer questions such as "How was my health in July?" or "Compare my finances in April and July" with exact, computed numbers.

### Agentic RAG with Two Knowledge Sources

A retrieval node uses an LLM router to decide, per question, whether to search:

* **`journal`**: the user's own diary entries, for "why did this happen" questions
* **`knowledge_base`**: general guidance and metric definitions, for "what does this mean / what should I do" questions
* **both**, or **neither** (for example, a greeting or a request that only needs exact numbers)

The router also rewrites the question into a clean search query and can select a specific month, which is applied as a metadata filter.

### Validated Structured Action Decisions

The Insight Agent returns a Pydantic-validated object (summary, action, reasoning) instead of free text that is searched for keywords. The action is restricted to an enum (`none`, `doctor`, `financial_planner`, `both`), and a guardrail overrides any action for a domain that was not analyzed in that run.

### Observability

Every run is traced with **LangSmith**, making routing decisions, MCP tool calls and arguments, prompts, token usage, and latency visible per node.

### Resilience

* A reset node clears per-question state so results do not leak between questions on the same conversation thread
* Domain agents retry once if the final message is empty, then fall back to summarizing the raw tool output
* The retrieval router retries once, then falls back to searching both sources with a deterministic month guess
* The insight agent falls back to "no action" if structured output fails, instead of crashing the graph

---

## Specialized Domain Agents

#### Health Agent

Analyzes sleep, steps, resting heart rate, active minutes, calories burned, stress, and mood.

#### Finance Agent

Analyzes daily spending, account balance, savings rate, credit utilization, and financial stress.

#### Productivity Agent

Analyzes focus score, deep work hours, tasks completed, meeting hours, context switches, and burnout risk.

---

## Synthetic Data

The project uses synthetic data instead of real personal information. There are two kinds.

### Structured data (read by MCP tools)

Daily records from **2026-04-01 to 2026-10-25** for each domain:

```text
data/
├── health.json
├── finance.json
└── productivity.json
```

The data is generated from a shared underlying "life quality" signal plus noise, so the three domains correlate realistically. Several deliberate rough patches are built in, and some affect only one domain so that cross-domain reasoning has something to distinguish:

| Period | Domains affected |
| ------ | ---------------- |
| Apr 21 to May 1 | health, finance, productivity |
| May 20 to Jun 2 | finance only |
| Jun 10 to Jun 20 | health, finance, productivity |
| Jul 1 to Jul 10 | health only |
| Aug 3 to Aug 14 | health, finance, productivity |
| Sep 1 to Sep 10 | productivity only |
| Oct 12 to Oct 21 | health, finance |

Each dip fades over a few days rather than snapping back. The generator uses a fixed random seed, so the data is reproducible.

### Unstructured data (indexed for RAG)

```text
data/
├── journal/
│   └── journal.txt          # dated diary entries explaining what happened
└── knowledge/
    └── *.txt                # guidance and metric definitions (sleep, savings rate, burnout, ...)
```

* The **journal** gives causes ("deadline crunch, slept five hours, ordered takeout") that numbers alone cannot provide
* The **knowledge files** define the metrics as this app uses them and give general guidance. Thresholds such as "stress above 50 is high" are this app's own alarm levels, not clinical or financial standards

---

## MCP Architecture

The domain agents do not read the JSON files directly. Each domain exposes its data through a dedicated **FastMCP server**.

```text
Health Agent
     │
     ▼
MCP Client
     │
     ▼
Health MCP Server
     │
     ▼
health.json
```

The same pattern is used for Finance and Productivity.

### MCP Tools (health shown; finance and productivity mirror it)

```text
get_health_data(days, start_date, end_date)        raw daily records
get_health_stats(days, start_date, end_date)       average / min / max per metric
compare_health_trend(days, start_date, end_date)   first half vs second half of one period
compare_health_periods(start_a, end_a, start_b, end_b)   two separate periods, e.g. April vs July
```

The finance tools additionally report the latest account balance and balance change. A running balance is not averaged, because averaging a cumulative value is meaningless.

This keeps a clean separation:

```text
Agent  →  reasoning
MCP Tool  →  data access and exact computation
Data Source  →  JSON today; could be a database or API later
```

Heavy computation (averages, comparisons) happens inside the tools, so the LLM receives a small summary instead of dozens of raw records. This keeps token usage low and avoids relying on the LLM for arithmetic.

---

## Retrieval (Agentic RAG)

Numbers always come from the MCP tools. Retrieval supplies **text only**: the journal's causes and the knowledge base's guidance.

### How retrieval works

```text
Question
  → router LLM: picks source(s), rewrites the query, optionally picks a month
  → Chroma embeds the rewritten query
  → metadata filter (domain, month)
  → nearest-neighbor search over stored vectors
  → top-k chunks returned as text for the Insight Agent
```

| Component | Detail |
| --------- | ------ |
| Vector store | ChromaDB (persistent), two collections: `journal` and `knowledge_base` |
| Embeddings | Chroma's default `all-MiniLM-L6-v2` model (384 dimensions), run locally. The same model embeds stored text and queries |
| Index / distance | HNSW, with Chroma's default distance (squared L2). Smaller distance means closer |
| Chunking | One chunk per journal entry. Knowledge paragraphs are packed up to about 600 characters |
| Top-k | 3 from the journal, 2 from the knowledge base |
| Filtering | Journal search is filtered by routed domain (plus `general` entries) and by month when the router sets one |
| Router | LLM with JSON-schema structured output; retries once, then falls back |

### What this is not

This is dense semantic retrieval only. There is no keyword/BM25 search, no hybrid search, no reranking, and no similarity threshold. At roughly thirty journal entries and thirty knowledge chunks, those would add complexity without a real benefit. They would be the first things to add if the collections grew into the hundreds.

### Which questions reach which source

| Question type | Tools | Retrieval |
| ------------- | ----- | --------- |
| "What was my average sleep in July?" | stats for July | none |
| "What does a financial stress score mean?" | stats | knowledge |
| "Why was my June so stressful?" | stats for June | journal (month filter) |
| "Why was July bad for my health, and what helps?" | stats for July | journal and knowledge |

---

## LangGraph Workflow

The workflow is orchestrated with **LangGraph** using a shared typed state (`AgentState`).

```text
START
  │
  ▼
Reset            clears results from the previous question
  │
  ▼
Coordinator      selects relevant domains
  │
  ├──────────────┬──────────────┐
  ▼              ▼              ▼
Health         Finance       Productivity
  └──────────────┼──────────────┘
                 ▼
             Retrieval        (journal / knowledge / both / none)
                 │
                 ▼
              Insight         (validated action decision)
                 │
          ┌──────┴──────┐
        action        no action
          ▼              ▼
        Action          END
          │
          ▼
         END
```

Notes on the design:

* Each node returns only the keys it wants to change, and LangGraph merges them into the shared state
* The domain nodes use separate edges into `retrieval` instead of a wait-for-all join, because the coordinator may route only one or two domains, and a join on all three would hang
* A checkpointer keyed by `thread_id` keeps state per conversation. It is in-memory today and would be swapped for SQLite or Postgres in a real deployment

---

## Insight Agent

The Insight Agent combines the relevant domain reports and the retrieved context, looks for relationships across domains, and returns a Pydantic-validated result:

```text
summary    short plain-text overall summary
action     none | doctor | financial_planner | both
reasoning  one sentence explaining the choice
```

The action is based on the **domain reports** (the retrieved context is background only), and a guardrail overrides any action for a domain that was not analyzed in that run. For example, a productivity-only question can never book a doctor.

The objective is to move from data retrieval toward **cross-domain reasoning**: for example, noticing that a stretch of poor sleep, rising spending, and falling focus line up, and the journal explains why.

---

## Action Agent

The Action Agent extends the workflow beyond generating a text response. It reads the validated `action_decision` field (no text parsing) and:

1. Generates an **iCalendar `.ics` file** for a health check-up and/or a financial planner meeting
2. Emails it as an attachment through **SMTP**
3. Reports what was done back into the shared state

The `.ics` file opens in Outlook, Google Calendar, and other apps that support iCalendar.

```text
Insight Agent → validated action → Action Agent → .ics → SMTP → Calendar application
```

This is a **reminder to book a real appointment**, not an actual booking with a clinic or planner. The action functionality is a technical demonstration and should not be interpreted as a real medical or financial recommendation system.

---

## Observability (LangSmith)

Tracing is enabled with environment variables only, with no changes to the agent code:

```env
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_langsmith_key
LANGSMITH_PROJECT=personal-insight-agent
```

Each question becomes one trace showing the coordinator's routing prompt and answer, each domain agent's MCP tool calls and arguments (for example, which `start_date` and `end_date` it chose for "July"), the retrieval router's structured decision and the chunks fetched, and the Insight Agent's validated output, along with latency and token counts per step.

Note that prompts and data are sent to LangSmith's servers. That is fine for synthetic data, but worth considering before using real personal data.

---

## Docker

The application is containerized using **Docker** and **Docker Compose**.

```text
┌───────────────────────────────────────────────┐
│                 Docker Compose                │
│                                               │
│  Health Server        (port 8000)             │
│  Finance Server       (port 8001)             │
│  Productivity Server  (port 8002)             │
│  Web / Gradio         (port 7860)             │
│     └── ChromaDB index (built into the image) │
│                                               │
└───────────────────────────────────────────────┘
```

Things worth knowing:

* The MCP servers bind to `0.0.0.0` so other containers can reach them. Binding to `127.0.0.1` only accepts connections from inside the same container
* Containers reach each other by service name (for example `http://health-server:8000/mcp`), configured through environment variables with a localhost fallback for non-Docker runs
* The web image copies `data/` and runs the ingest script at build time, so the vector index is baked into the image and the first question is not slow
* Because the index is baked in, **rebuild the image after changing the journal or knowledge files** (`docker compose up --build`)

---

## Deployment

After developing and testing the application locally, the Dockerized application was also deployed to **Railway**.

The deployment process involved:

1. Containerizing the application
2. Configuring the application to use the deployment environment's port
3. Configuring environment variables
4. Running the MCP services
5. Running the web application
6. Testing the deployed application

The local Docker setup is used for the demo shown in this repository's walkthrough.

---

## Project Structure

A simplified version of the project structure is:

```text
Agentic_Project/
│
├── app/
│   ├── agents/
│   │   ├── coordinator.py
│   │   ├── health_agent.py
│   │   ├── finance_agent.py
│   │   ├── productivity_agent.py
│   │   ├── retrieval_agent.py
│   │   ├── insight_agent.py
│   │   └── action_agent.py
│   │
│   ├── graph/
│   │   ├── state.py
│   │   └── workflow.py
│   │
│   ├── rag/
│   │   ├── store.py          # Chroma client and the two collections
│   │   └── ingest.py         # builds embeddings from journal and knowledge files
│   │
│   ├── mcp/
│   │   └── reminder_client.py   # .ics generation and SMTP email
│   │
│   └── api/
│       └── main.py           # Gradio frontend
│
├── mcp_servers/
│   ├── health_server.py
│   ├── finance_server.py
│   └── productivity_server.py
│
├── data/
│   ├── health.json
│   ├── finance.json
│   ├── productivity.json
│   ├── journal/
│   │   └── journal.txt
│   └── knowledge/
│       └── *.txt
│
├── tests/
│
├── Dockerfile.web
├── Dockerfile.health
├── Dockerfile.finance
├── Dockerfile.productivity
├── docker-compose.yaml
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Tech Stack

| Technology              | Purpose                                                     |
| ----------------------- | ----------------------------------------------------------- |
| **Python**              | Application and agent development                           |
| **LangGraph**           | Multi-agent workflow orchestration and state management     |
| **LangChain**           | Agent, tool-calling, and LLM integration                    |
| **Groq**                | LLM inference                                               |
| **Open-source LLMs**    | Reasoning, routing, and summarization (GPT-OSS family)      |
| **FastMCP**             | MCP server implementation                                   |
| **MCP**                 | Tool/data access interface between agents and services      |
| **ChromaDB**            | Vector database for the journal and knowledge collections   |
| **Embeddings**          | `all-MiniLM-L6-v2` via Chroma's default embedding function  |
| **Pydantic**            | Schema-validated structured LLM outputs                     |
| **LangSmith**           | Tracing and observability                                   |
| **Gradio**              | User interface                                              |
| **Docker**              | Containerization                                            |
| **Docker Compose**      | Local multi-container orchestration                         |
| **SMTP**                | Email delivery for calendar actions                         |
| **iCalendar (.ics)**    | Calendar event generation                                   |
| **Railway**             | Cloud deployment                                            |

---

## Running Locally

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd Agentic_Project
```

### 2. Create a virtual environment

Windows:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key

# Email / calendar actions
GMAIL_ADDRESS=your_address@gmail.com
GMAIL_APP_PASSWORD=your_16_character_app_password
REMINDER_RECIPIENT=your_address@gmail.com

# Observability (optional)
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_langsmith_key
LANGSMITH_PROJECT=personal-insight-agent
```

Gmail requires an **app password** (not your normal password). **Do not commit `.env` to GitHub.**

### 5. Build the vector index

```bash
python -m app.rag.ingest
```

This embeds the journal and knowledge files into `chroma_db/`. If you change those files, delete `chroma_db/` and run it again.

### 6. Start the services (without Docker)

Run each from the project root, in separate terminals:

```bash
python -m mcp_servers.health_server
python -m mcp_servers.finance_server
python -m mcp_servers.productivity_server
python -m app.api.main
```

---

## Running with Docker Compose

Build the containers:

```bash
docker compose build
```

Start the complete application:

```bash
docker compose up
```

The Gradio application should then be available at:

```text
http://localhost:7860
```

To rebuild after changing code or data:

```bash
docker compose up --build
```

To run in detached mode:

```bash
docker compose up -d
```

To view logs:

```bash
docker compose logs -f
```

To stop the application:

```bash
docker compose down
```

The `.env` file is not copied into the images. Environment variables are passed to the `web` service through `docker-compose.yaml`.

---

## Example Queries

The data covers 2026-04-01 to 2026-10-25.

### Exact numbers (tools only)

```text
What was my average sleep in July?
Compare my finances in April and July.
How has my productivity been this month?
```

### Meaning and guidance (knowledge base)

```text
What does a financial stress score mean?
When should I see a financial planner?
What are the warning signs of burnout?
```

### Causes (journal)

```text
Why was my June so stressful?
What was going on in early September at work?
```

### Causes plus guidance (both sources)

```text
Why was July bad for my health, and what helps?
I had a rough August. What caused it and what should I do?
```

### Action-oriented

```text
Have I been doing okay financially lately?
How was my health in June? Should I see a doctor?
```

This demonstrates the Insight → Action workflow and calendar `.ics` generation. Because the decision comes from an LLM, an action is not guaranteed for every phrasing.

### Edge cases

```text
Hi                                  (no tools, no retrieval, no action)
How was my health in December?      (tool returns an error with the available range)
```

---

## Example End-to-End Flow

```text
User: "Why was July bad for my health, and what helps?"
                │
                ▼
        Coordinator Agent  →  health
                │
                ▼
          Health Agent  →  get_health_stats(start_date=2026-07-01, end_date=2026-07-31)
                │
                ▼
        Retrieval Agent (router)
          sources = journal + knowledge, month = 2026-07
                │
                ▼
          Insight Agent
          summary + validated action = doctor
                │
                ▼
          Action Agent  →  .ics  →  SMTP  →  reminder email
```

---

## Design Decisions and Tradeoffs

**RAG was first built over the JSON data, then replaced.** The first version embedded weekly text summaries generated from the JSON and searched them. In testing, the retrieved weeks often did not match the question, because embeddings match wording rather than numbers. Adding date-range parameters to the MCP tools solved the same problems exactly and deterministically, so the weekly-summary collection was removed. RAG was kept for the content that tools cannot provide: unstructured text (journal entries and guidance).

**Numbers come from tools, text comes from retrieval.** The LLM never does arithmetic over raw records, and retrieval never returns statistics.

**Structured outputs replaced keyword matching.** The action decision used to be inferred by searching the LLM's text for a phrase like "action: doctor", which could silently miss. It is now a schema-validated enum with a domain guardrail.

**Fan-out uses separate edges, not a join.** Waiting for all three domain agents would hang when the coordinator routes only one.

**Free-tier constraints shaped the design.** Rate limits and model deprecations on a free LLM tier led to small tool outputs, per-question routing, retries, and fallbacks, and to checking the live model list rather than trusting hardcoded names.

---

## Why This Project?

The main goal of this project was to understand the engineering involved in an agentic AI system rather than simply building an application around a single LLM call.

Some of the questions I wanted to explore were:

* How should an agent decide which specialist should handle a request?
* How can multiple specialized agents collaborate?
* How should state be maintained across an agent workflow?
* How can agents access external data through tools?
* Where does MCP fit into an agent architecture?
* When is retrieval the right tool, and when is a deterministic tool better?
* How can an agent choose between multiple knowledge sources?
* How can an agent move from reasoning to taking an action reliably?
* How should a multi-service agent application be containerized?
* What changes when the application moves from local development to cloud deployment?

---

## What I Learned

The biggest takeaway from this project was that an agentic AI application is more than an LLM.

The LLM provides reasoning capabilities, but the surrounding engineering determines how that reasoning becomes a reliable workflow.

Building this project gave me hands-on experience with:

* Multi-agent orchestration and conditional routing
* Shared agent state and per-question state reset
* Tool calling and MCP architecture with FastMCP servers
* Designing a tool API (raw data, aggregates, comparisons, date ranges) to control context size
*
