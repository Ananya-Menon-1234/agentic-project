# Personal Insight Agent

A multi-agent AI system that analyzes synthetic **health, finance, and productivity data** and generates cross-domain insights using specialized AI agents.

The project was built to explore the engineering behind an agentic AI application — including **agent orchestration, state management, MCP-based tool access, action execution, containerization, and cloud deployment**.

> **Note:** All health, financial, and productivity data used in this project is synthetic and generated for demonstration purposes. It is not intended for real medical, financial, or productivity recommendations.

---

## Overview

Personal data is often spread across different sources. A health application may contain sleep and activity information, a financial application may contain spending information, and productivity tools may contain information about focus and workload.

This project explores whether a multi-agent system can bring these domains together and provide a higher-level view.

Instead of using one large agent for everything, the system uses specialized agents:

* **Coordinator Agent** — determines which domains are relevant to a user's question
* **Health Agent** — analyzes health-related data
* **Finance Agent** — analyzes financial data
* **Productivity Agent** — analyzes productivity data
* **Insight Agent** — combines the domain-level reports and identifies cross-domain patterns
* **Action Agent** — determines whether an action should be taken

The overall workflow is:

                         User
                           │
                           ▼
                  ┌─────────────────┐
                  │ Coordinator     │
                  │ Agent           │
                  └────────┬────────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────────┐
        │  Health  │ │ Finance  │ │ Productivity │
        │  Agent   │ │  Agent   │ │    Agent     │
        └────┬─────┘ └────┬─────┘ └──────┬───────┘
             │            │              │
             ▼            ▼              ▼
        Health MCP   Finance MCP   Productivity MCP
             │            │              │
             ▼            ▼              ▼
        health.json  finance.json  productivity.json
             │            │              │
             └────────────┼──────────────┘
                          ▼
                 ┌─────────────────┐
                 │ Insight Agent   │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │ Action Agent    │
                 └────────┬────────┘
                          │
                          ▼
                        Answer

---

## Key Features

### Dynamic Agent Routing

The Coordinator Agent determines which domain agents need to execute based on the user's question.

For example:

"How has my productivity been this month?" --> Coordinator Agent -->  Productivity Agent


Whereas:

"How am I doing overall across my health, finances and productivity?" --> Coordinator Agent --> Health + Finance + Productivity

This prevents unnecessary agents from running for every query.

---

### Specialized Domain Agents

Each domain has its own specialized agent.

#### Health Agent

Analyzes:

* Sleep
* Steps
* Resting heart rate
* Active minutes
* Calories burned
* Stress
* Mood

#### Finance Agent

Analyzes:

* Daily spending
* Account balance
* Savings rate
* Credit utilization
* Financial stress

#### Productivity Agent

Analyzes:

* Focus score
* Deep work hours
* Tasks completed
* Meeting hours
* Context switches
* Burnout risk

---

## Synthetic Data

The project uses synthetic JSON data instead of real personal information.

The datasets cover September and contain daily records for each domain.


data/
├── health.json
├── finance.json
└── productivity.json


### Creating a Meaningful Pattern

Rather than generating completely random data, the datasets intentionally contain a period around **September 10–18** where multiple indicators deteriorate together.

For example:


Health
    ↓
Lower sleep
Higher stress
Lower mood

Finance
    ↓
Higher spending
Higher financial stress

Productivity
    ↓
Lower focus
Lower deep work
More context switching
Higher burnout risk


This creates a synthetic "rough patch" that the Insight Agent can identify across domains.

The purpose is not to establish medically or financially meaningful thresholds. The purpose is to create a dataset where the multi-agent system has meaningful patterns to reason about.

---

## MCP Architecture

The domain agents do not directly read the JSON files.

Instead, each domain exposes its data through a dedicated **FastMCP server**.


Health Agent --> MCP Client --> Health MCP Server --> health.json


The same pattern is used for Finance and Productivity.

### Health MCP Tools

The Health MCP server exposes tools such as:

get_health_data()
get_health_stats()
compare_health_trend()


The corresponding Finance and Productivity MCP servers expose domain-specific tools.

This creates a separation between:


Agent
  │
  │ reasoning
  ▼
MCP Tool
  │
  │ data access
  ▼
Data Source


One advantage of this approach is that the underlying data source can be changed later.

For example:


JSON
 ↓
Database
 ↓
External API
 ↓
Wearable API


without fundamentally changing the agent's reasoning layer.

---

## LangGraph Workflow

The overall workflow is orchestrated using **LangGraph**.

The graph contains nodes for:


Coordinator
Health
Finance
Productivity
Insight
Action


The Coordinator uses conditional routing to determine which domain agents should execute.

The domain agents then populate the shared graph state with their reports.

The Insight Agent consumes those reports and produces a combined insight.

Finally, the Action Agent can determine whether an external action should be performed.

Conceptually:


START
  │
  ▼
Coordinator
  │
  ├──────────────┐
  │              │
  ▼              ▼
Health         Finance       Productivity
  │              │              │
  └──────────────┼──────────────┘
                 ▼
              Insight
                 │
                 ▼
              Action
                 │
                 ▼
                END


---

## Insight Agent

The Insight Agent is responsible for combining the outputs of the relevant domain agents.

For example, the individual agents might identify:


Health:
Sleep decreased and stress increased.

Productivity:
Focus and deep-work hours decreased while
context switching increased.

Finance:
Spending and financial stress increased.


Instead of returning three independent reports, the Insight Agent looks for relationships between them.

The resulting insight might identify a broader pattern such as:


A period of increased stress appears to coincide
with lower sleep, reduced focus and increased
financial pressure.


The objective is to move from simple data retrieval toward **cross-domain reasoning**.

---

## Action Agent

The Action Agent extends the workflow beyond generating a text response.

The Insight Agent can produce an action decision:


ACTION: none

ACTION: doctor

ACTION: financial_planner

ACTION: both


The Action Agent then handles the selected action.

For the calendar workflow, the application can generate an **iCalendar `.ics` file** containing the appointment information.

The `.ics` file can then be sent through **SMTP** and opened using calendar applications such as:

* Microsoft Outlook
* Google Calendar
* Other applications supporting the iCalendar format

Conceptually:


Insight Agent
      │
      ▼
Action Decision
      │
      ▼
Action Agent
      │
      ▼
Generate .ics
      │
      ▼
SMTP
      │
      ▼
Calendar Application


This demonstrates an important agentic pattern:


Observation
     ↓
Reasoning
     ↓
Decision
     ↓
Action


The action functionality is intended as a technical demonstration and should not be interpreted as an actual medical or financial recommendation system.

---

## Docker

The application is containerized using **Docker** and **Docker Compose**.

The local setup consists of multiple services:


┌───────────────────────────────┐
│         Docker Compose        │
│                               │
│  ┌───────────────┐            │
│  │ Health Server │            │
│  └───────────────┘            │
│                               │
│  ┌───────────────┐            │
│  │ Finance Server│            │
│  └───────────────┘            │
│                               │
│  ┌─────────────────────┐      │
│  │ Productivity Server │      │
│  └─────────────────────┘      │
│                               │
│  ┌───────────────┐            │
│  │ Web / Gradio  │            │
│  └───────────────┘            │
│                               │
└───────────────────────────────┘


Docker Compose allows the complete application to be started as a group rather than manually launching each service.

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


Agentic_Project/
│
├── app/
│   ├── agents/
│   │   ├── coordinator.py
│   │   ├── health_agent.py
│   │   ├── finance_agent.py
│   │   ├── productivity_agent.py
│   │   ├── insight_agent.py
│   │   └── action_agent.py
│   │
│   ├── graph/
│   │   ├── state.py
│   │   └── workflow.py
│   │
│   └── api/
│       └── main.py
│
├── mcp_servers/
│   ├── health_server.py
│   ├── finance_server.py
│   └── productivity_server.py
│
├── data/
│   ├── health.json
│   ├── finance.json
│   └── productivity.json
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


---

## Tech Stack

| Technology           | Purpose                                                 |
| -------------------- | ------------------------------------------------------- |
| **Python**           | Application and agent development                       |
| **LangGraph**        | Multi-agent workflow orchestration and state management |
| **LangChain**        | Agent and LLM integration                               |
| **Groq**             | LLM inference                                           |
| **Open-source LLMs** | Language reasoning                                      |
| **FastMCP**          | MCP server implementation                               |
| **MCP**              | Tool/data access interface between agents and services  |
| **Gradio**           | User interface                                          |
| **Docker**           | Containerization                                        |
| **Docker Compose**   | Local multi-container orchestration                     |
| **SMTP**             | Email delivery for calendar actions                     |
| **iCalendar (.ics)** | Calendar event generation                               |
| **Railway**          | Cloud deployment                                        |

---

## Running Locally

### 1. Clone the repository

bash
git clone <your-repository-url>
cd Agentic_Project


### 2. Create a virtual environment

Windows:

powershell
python -m venv .venv


Activate it:

powershell
.\.venv\Scripts\Activate.ps1


Linux/macOS:

bash
python -m venv .venv
source .venv/bin/activate


### 3. Install dependencies

bash
pip install -r requirements.txt


### 4. Configure environment variables

Create a `.env` file in the project root.

Example:

env
GROQ_API_KEY=your_groq_api_key


If email/calendar actions are enabled, configure the required SMTP variables as well.

**Do not commit `.env` to GitHub.**

---

## Running with Docker Compose

Build the containers:

bash
docker compose build


Start the complete application:

bash
docker compose up


The Gradio application should then be available at:


http://localhost:7860


To run the services in detached mode:

bash
docker compose up -d


To view logs:

bash
docker compose logs -f


To stop the application:

bash
docker compose down


---

## Example Queries

### Domain-specific query


How has my productivity been this month?


Expected routing:


Coordinator
    ↓
Productivity Agent
    ↓
Productivity MCP
    ↓
Insight
    ↓
Answer


### Cross-domain query


How am I doing overall across my health,
finances and productivity this month?


Expected routing:


Coordinator
    ↓
┌────────┬─────────┬───────────────┐
Health   Finance   Productivity
└────────┴─────────┴───────────────┘
                ↓
             Insight
                ↓
             Answer


### Action-oriented query


My stress and financial stress seem high this month.
Should I consider speaking to a doctor or financial planner?


This can demonstrate the Insight → Action workflow and calendar `.ics` generation.

---

## Example End-to-End Flow

A typical request follows this path:


User:
"How am I doing overall this month?"
                │
                ▼
        Coordinator Agent
                │
       ┌────────┼────────┐
       ▼        ▼        ▼
    Health   Finance  Productivity
       │        │        │
       ▼        ▼        ▼
     MCP      MCP      MCP
       │        │        │
       └────────┼────────┘
                ▼
          Insight Agent
                │
                ▼
          Action Agent
                │
                ▼
        Final Response


---

## Why This Project?

The main goal of this project was to understand the engineering involved in an agentic AI system rather than simply building an application around a single LLM call.

Some of the questions I wanted to explore were:

* How should an agent decide which specialist should handle a request?
* How can multiple specialized agents collaborate?
* How should state be maintained across an agent workflow?
* How can agents access external data through tools?
* Where does MCP fit into an agent architecture?
* How can an agent move from reasoning to taking an action?
* How should a multi-service agent application be containerized?
* What changes when the application moves from local development to cloud deployment?

---

## What I Learned

The biggest takeaway from this project was that an agentic AI application is more than an LLM.

The LLM provides reasoning capabilities, but the surrounding engineering determines how that reasoning becomes a reliable workflow.

Building this project gave me hands-on experience with:

* Multi-agent orchestration
* Conditional routing
* Shared agent state
* Tool calling
* MCP architecture
* FastMCP servers
* Cross-agent reasoning
* Action execution
* Calendar integrations
* Docker containerization
* Docker Compose
* Cloud deployment

---

## Author

**Ananya Menon**

Built as a hands-on exploration of **Agentic AI, multi-agent systems, MCP, LangGraph and AI application deployment**.
