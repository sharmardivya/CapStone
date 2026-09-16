# A2A Travel Planner — modular version

The code from [`a2a_langgraph_travel_planner.ipynb`](../a2a_langgraph_travel_planner/a2a_langgraph_travel_planner.ipynb),
split into small Python files (one job per file), extended with an **HR Leave Agent**, plus a
chatbot that runs in the browser.

A LangGraph orchestrator sends the user's request to four specialist agents over the
**A2A protocol** and combines their answers into one travel plan that ends with the
employee's leave balance:

```
User: "Plan a 5-day trip to Tokyo for employee E1001"
   │
   ▼  LangGraph StateGraph
parse_query ──(destination or employee ID missing)──► asks the user only for what is missing
   │
check_leave_balance ─── A2A ──► HR Leave Agent             :8004  (LangChain + SQLite)
   │   └──(employee ID not in HR database)──► asks for a valid employee ID
   │
research_destination ── A2A ──► Destination Research Agent :8001  (LangChain + Wikipedia)
   │
check_weather ───────── A2A ──► Weather Intelligence Agent :8002  (LangChain + wttr.in)
   │
estimate_budget ─────── A2A ──► Budget Estimator Agent     :8003  (LangChain + cost table)
   │
synthesize_plan ──► travel plan + leave balance
```

## Run it

All commands run **from this folder**. No `Activate.ps1` needed — `uv run` uses the project's `.venv`.

```powershell
cd C:\Divya\code\CapStone\Capstone_Project_Sep26\a2a_travel_planner_modular
uv run python run_chatbot.py          # opens http://127.0.0.1:7860 in your browser
```

`.env` in this folder must contain `OPENAI_API_KEY=sk-...` (see `.env.example`).
On a new machine, run `uv sync` once first.

| Command | What it does |
|---|---|
| `uv run python run_chatbot.py` | Browser chatbot |
| `uv run python run_cli.py "Plan a 5-day trip to Tokyo" --employee-id E1001` | One plan in the terminal, plus audit table |
| `uv run python run_cli.py "Plan 7 days in Bali for employee E1002" --diagram` | Employee ID inside the query; also saves `outputs/a2a_langgraph_flow.png` |
| `uv run python run_agents.py` | Only start the 4 agents and keep them running |
| `uv run python -m travel_planner.data.leave_db` | Create the leave database and print it |
| `uv run python -m examples.discover_agents` | Read each agent's AgentCard (no LLM cost) |
| `uv run python -m examples.test_agents` | Call each agent on its own over A2A |
| `uv run python -m examples.inspect_state` | Print the full LangGraph state after a run |
| `uv run python -m examples.inspect_protocol` | Show the raw JSON-RPC request and response |

The chatbot and CLI start the agents automatically. If `run_agents.py` is already running in
another terminal, they reuse those agents instead.

## Talking to the chatbot

The chatbot asks for whatever it still needs and remembers your earlier answers:

```
You:  I want to visit Bali for 7 days
Bot:  Got it — 7 days in Bali. What's your employee ID (e.g. E1001)?
You:  E17071
Bot:  ⚠️ No employee found with ID 'E17071'. Valid employee IDs: E1001, … Please send a valid employee ID.
You:  E1002
Bot:  (full travel plan, ending with Rahul's leave balance)
```

An employee ID is `E` followed by digits. In the CLI, pass it with `--employee-id` or write it in
the query. After a plan is delivered, the next chat message starts a new request.

## The leave database

The HR Leave Agent reads a synthetic SQLite database, `travel_planner/data/hr_leave.db`, created
automatically when the agent starts. Table `leave_balance`, key `employee_id`, balances in days:

| employee_id | name | department | annual_leave | casual_leave | sick_leave |
|---|---|---|---|---|---|
| E1001 | Asha Verma | Engineering | 18 | 6 | 10 |
| E1002 | Rahul Mehta | Finance | 4 | 2 | 8 |
| E1003 | Priya Nair | Marketing | 12 | 5 | 7 |
| E1004 | Karan Singh | Sales | 0 | 3 | 5 |
| E1005 | Neha Kapoor | Human Resources | 25 | 8 | 12 |

Try E1002 or E1004 with a 5-day trip to see the plan warn that the leave does not cover it.

## Folder structure

```
a2a_travel_planner_modular/
├── run_chatbot.py              entry point: browser chatbot
├── run_cli.py                  entry point: plan one trip in the terminal
├── run_agents.py               entry point: start the 4 agents only
├── .env / .env.example         OpenAI key
├── examples/                   one demo per notebook test section
│   ├── discover_agents.py
│   ├── test_agents.py
│   ├── inspect_state.py
│   └── inspect_protocol.py
└── travel_planner/
    ├── config.py               model, ports, URLs, timeouts, database path, employee ID format
    ├── llm.py                  ChatOpenAI clients + API-key check
    ├── a2a/                    protocol layer (knows nothing about travel)
    │   ├── models.py           AgentCard, Message, JSON-RPC models
    │   ├── server.py           create_a2a_app(): handler → A2A FastAPI server
    │   ├── client.py           A2AClient: discover() and send()
    │   └── server_runner.py    run a FastAPI app in a background thread
    ├── tools/                  LangChain tools
    │   ├── wikipedia_tool.py
    │   ├── weather_tool.py
    │   ├── cost_tool.py
    │   └── leave_tool.py       leave balance lookup (SQLite)
    ├── data/
    │   ├── cost_db.py          offline daily cost table
    │   └── leave_db.py         synthetic SQLite leave database (5 employees)
    ├── agents/                 the four A2A agents
    │   ├── destination_agent.py    :8001
    │   ├── weather_agent.py        :8002
    │   ├── budget_agent.py         :8003
    │   ├── hr_agent.py             :8004
    │   ├── agent_runner.py     send one prompt to a LangChain agent
    │   └── launcher.py         start all agents, wait until ready
    ├── orchestrator/           LangGraph
    │   ├── state.py            TravelState (includes employee_id and leave_info)
    │   ├── audit_log.py        record of completed tasks
    │   ├── graph.py            build the graph, plan_trip(query, employee_id)
    │   └── nodes/              one file per node, in run order
    │       ├── parse_query.py
    │       ├── check_leave_balance.py
    │       ├── research_destination.py
    │       ├── check_weather.py
    │       ├── estimate_budget.py
    │       ├── synthesize_plan.py
    │       └── a2a_call.py     shared helper for the four agent-calling nodes
    ├── reporting/
    │   ├── audit_report.py     task table (text)
    │   └── flow_diagram.py     architecture + timing chart (PNG)
    └── chatbot/
        └── app.py              Gradio chat UI that asks for missing details
```

## Where each notebook section went

| Notebook section | File(s) |
|---|---|
| 1 — Setup, LLM setup, key check | `config.py`, `llm.py` |
| 2 — A2A data models | `a2a/models.py` |
| 3 — A2A factory, client, registry | `a2a/server.py`, `a2a/client.py`, `config.AGENT_REGISTRY` |
| 4 — The LangChain agents | `agents/*_agent.py`, `tools/*`, `data/*` |
| 5 — LangGraph state, nodes, graph | `orchestrator/state.py`, `orchestrator/nodes/*`, `orchestrator/graph.py` |
| 6 — Start agent servers | `a2a/server_runner.py`, `agents/launcher.py`, `run_agents.py` |
| 7 — Agent discovery | `examples/discover_agents.py` |
| 8 — Test individual agents | `examples/test_agents.py` |
| 9 — End-to-end demo | `run_cli.py`, `run_chatbot.py` |
| 10 — Audit table + diagram | `reporting/audit_report.py`, `reporting/flow_diagram.py` |
| 11 — State + raw protocol inspection | `examples/inspect_state.py`, `examples/inspect_protocol.py` |

## Differences from the notebook

- **HR Leave Agent (new).** A fourth A2A agent on port 8004 reads a SQLite leave database. The
  pipeline takes an employee ID, checks leave first, and the final plan ends with a Leave Balance section.
- **The chatbot asks for missing details.** The notebook silently planned a trip to Paris when it
  could not find a destination. Now the bot asks only for what is missing (destination or employee
  ID) and remembers the rest of the request.
- **An agent being down no longer crashes the pipeline.** The node records a warning and the
  plan is written from the other agents' answers.
- **Wikipedia is called directly with a descriptive User-Agent.** The notebook's `WikipediaQueryRun`
  uses the `wikipedia` package, which Wikipedia now rate-limits (HTTP 429), so research failed with
  "Expecting value: line 1 column 1". A failed lookup is now reported to the agent as text.
- **Each agent has its own OpenAI client, and LLM calls time out after 60 s.** Sharing one client
  between the agents' event loops made the final synthesis step hang.
- **Agent step-by-step debug output is off by default.** Set `AGENT_DEBUG=true` in `.env`.
- **Diagram labels have no emojis**, which removes matplotlib's "Glyph missing from font" warnings.

## Troubleshooting

- **`Port 8001 is used by another program`** — another copy (an older chatbot, or the notebook's
  kernel) is still running its agents. Stop it, then try again.
- **`OpenAI API key check failed`** — the message says why (invalid key, no credit, no internet).
- **Chatbot port 7860 busy** — set `CHATBOT_PORT=7861` in `.env`.
