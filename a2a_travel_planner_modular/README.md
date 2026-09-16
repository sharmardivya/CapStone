# A2A Travel Planner

A multi-agent travel planning chatbot. You ask for a trip, for example
*"Plan a 5-day trip to Tokyo for employee E1001"*, and get one plan that covers the destination,
weather, budget **and** whether you have enough leave for it.

A **LangGraph orchestrator** calls four independent AI agents over the **A2A (Agent-to-Agent)
protocol**. Each agent is its own small web service with one job:

```
Browser chatbot (Gradio)
        │
        ▼
LangGraph orchestrator
  parse_query ──(destination or employee ID missing)──► asks you only for what is missing
        │
  check_leave_balance ─── A2A ──► HR Leave Agent             :8004  (SQLite leave database)
        │   └──(employee ID not found)──► asks for a valid employee ID
        │
  research_destination ── A2A ──► Destination Research Agent :8001  (Wikipedia)
        │
  check_weather ───────── A2A ──► Weather Intelligence Agent :8002  (wttr.in)
        │
  estimate_budget ─────── A2A ──► Budget Estimator Agent     :8003  (offline cost table)
        │
  synthesize_plan ──► travel plan + leave balance
```

**Built with:** Python 3.12 · LangGraph · LangChain · OpenAI `gpt-4o-mini` · FastAPI · Gradio · SQLite

---

## Contents

1. [Run locally](#1-run-locally)
2. [Deploy on Render](#2-deploy-on-render)
3. [Using the chatbot](#3-using-the-chatbot)
4. [Configuration](#4-configuration)
5. [Project structure](#5-project-structure)
6. [Troubleshooting](#6-troubleshooting)
7. [Documentation](#7-documentation)

---

## 1. Run locally

### Prerequisites

- Python 3.12 or later
- An OpenAI API key — create one at https://platform.openai.com/api-keys
- Internet access (OpenAI, Wikipedia, wttr.in)

### Step 1 — Get the code

```bash
git clone https://github.com/sharmardivya/CapStone.git
cd CapStone
git checkout a2a-travel-planner
cd a2a_travel_planner_modular
```

### Step 2 — Add your OpenAI key

Copy `.env.example` to `.env` and put your key in it:

```bash
# Windows
copy .env.example .env
# macOS / Linux
cp .env.example .env
```

```
OPENAI_API_KEY=sk-...your-key...
```

`.env` is listed in `.gitignore`, so the key is never committed.

### Step 3 — Install and run

**Option A — with `uv` (recommended).** No virtual-environment activation needed.

```bash
uv sync                         # creates .venv and installs the exact pinned versions
uv run python run_chatbot.py    # opens http://127.0.0.1:7860 in your browser
```

Install `uv` first if you don't have it: https://docs.astral.sh/uv/getting-started/installation/

**Option B — with `pip`.** Also works without running `Activate.ps1`:

```bash
python -m venv .venv

# Windows
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python run_chatbot.py

# macOS / Linux
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python run_chatbot.py
```

The chatbot starts the four agents automatically, waits until all are ready (about 5 seconds),
then opens in your browser. Press `Ctrl+C` in the terminal to stop.

### Other commands

With `uv`, run these from the `a2a_travel_planner_modular` folder
(with `pip`, replace `uv run python` by `.venv\Scripts\python` or `.venv/bin/python`):

| Command | What it does |
|---|---|
| `uv run python run_chatbot.py` | Browser chatbot |
| `uv run python run_cli.py "Plan a 5-day trip to Tokyo" --employee-id E1001` | One plan in the terminal, plus an audit table |
| `uv run python run_cli.py "Plan 7 days in Bali for employee E1002" --diagram` | Same, and saves a flow diagram to `outputs/` |
| `uv run python run_agents.py` | Start only the four agents and keep them running |
| `uv run python -m travel_planner.data.leave_db` | Create the HR leave database and print it |
| `uv run python -m examples.discover_agents` | Show each agent's AgentCard (no OpenAI cost) |
| `uv run python -m examples.test_agents` | Call each agent on its own |
| `uv run python -m examples.inspect_state` | Print the full workflow state after a run |
| `uv run python -m examples.inspect_protocol` | Show the raw A2A JSON-RPC request and response |

---

## 2. Deploy on Render

The whole application runs as **one Render web service**. The four agents start inside it on
internal ports 8001–8004 (never exposed); only the chatbot is public, on the port Render provides.
The code detects Render automatically through the `PORT` variable: it then listens on `0.0.0.0`
and does not try to open a browser.

### Before you start

1. **Push this branch to GitHub** (Render deploys from your repository):

   ```bash
   git push -u origin a2a-travel-planner
   ```

2. Have your **OpenAI API key** ready.
3. Create a free account at https://render.com and connect your GitHub account.

### Option A — Create the web service in the dashboard (recommended)

1. In the Render Dashboard click **New → Web Service**.
2. Select the repository **`sharmardivya/CapStone`**.
3. Fill in the settings:

   | Setting | Value |
   |---|---|
   | **Name** | `a2a-travel-planner` (any name) |
   | **Branch** | `a2a-travel-planner` |
   | **Root Directory** | `a2a_travel_planner_modular` |
   | **Language / Runtime** | `Python 3` |
   | **Build Command** | `pip install -r requirements.txt` |
   | **Start Command** | `python run_chatbot.py --no-browser` |
   | **Instance Type** | `Free` (use `Starter` if you see out-of-memory errors) |

4. Under **Environment Variables** add:

   | Key | Value |
   |---|---|
   | `OPENAI_API_KEY` | your OpenAI key |
   | `PYTHON_VERSION` | `3.12.12` |

5. Optional, under **Advanced**: set **Health Check Path** to `/`.
6. Click **Create Web Service**.

### Option B — Deploy with the Blueprint (`render.yaml`)

`render.yaml` in this folder contains the same settings.

1. In the Render Dashboard click **New → Blueprint**.
2. Select the repository and the branch `a2a-travel-planner`.
3. Set the **Blueprint file path** to `a2a_travel_planner_modular/render.yaml`.
   If your Render screen has no path field, copy `render.yaml` to the repository root, commit and push.
4. Enter your `OPENAI_API_KEY` when Render asks for it, then click **Apply**.

### Check the deployment

The first build takes a few minutes. In the service's **Logs** tab a successful start looks like this:

```
run_chatbot: OpenAI key OK (model replied 'OK')
travel_planner.agents.launcher: All 4 agents are ready
run_chatbot: Chatbot at http://0.0.0.0:10000  (Ctrl+C to stop)
```

Open the URL shown at the top of the service page (`https://<your-service>.onrender.com`) and ask
for a trip.

### Good to know on Render

- **Free services sleep** after 15 minutes without traffic. The next visit wakes the service,
  which takes about a minute, because the agents start again.
- **The public URL is open to anyone who has it**, and every plan uses your OpenAI credit.
  Set a monthly usage limit at https://platform.openai.com/settings/organization/limits.
- **Files are not permanent.** The HR leave database is sample data and is recreated
  automatically each time the service starts; generated diagrams are lost on restart.
- **Redeploying:** every push to the `a2a-travel-planner` branch triggers a new deploy.
- **Updating dependencies:** Render installs from `requirements.txt`. After changing packages with
  `uv add <package>`, regenerate it and commit both files:

  ```bash
  uv export --format requirements-txt --no-hashes --no-dev --no-emit-project -o requirements.txt
  ```

---

## 3. Using the chatbot

Write a trip request in plain English. If something is missing, the chatbot asks for **only**
that, and remembers what you already said:

```
You:  I want to visit Bali for 7 days
Bot:  Got it — 7 days in Bali. What's your employee ID (e.g. E1001)?
You:  E17071
Bot:  ⚠️ No employee found with ID 'E17071'. Valid employee IDs: E1001, E1002, E1003, E1004, E1005.
      Please send a valid employee ID.
You:  E1002
Bot:  (full travel plan for Bali, ending with Rahul's leave balance)
```

Click an example below the chat to copy it into the message box, edit it if you like, then send.
While a plan is being built, the reply shows which agent is working. A plan takes about
20–30 seconds; after it is delivered, your next message starts a new request.

**Every plan contains:** trip highlights · day-by-day itinerary · weather and packing ·
budget · attractions · travel tips · **leave balance** (and whether it covers the trip).

### Sample employees (synthetic HR database)

The HR Leave Agent reads a SQLite database created automatically on start-up.
Table `leave_balance`, key `employee_id`, balances in days:

| employee_id | name | department | annual_leave | casual_leave | sick_leave |
|---|---|---|---|---|---|
| E1001 | Asha Verma | Engineering | 18 | 6 | 10 |
| E1002 | Rahul Mehta | Finance | 4 | 2 | 8 |
| E1003 | Priya Nair | Marketing | 12 | 5 | 7 |
| E1004 | Karan Singh | Sales | 0 | 3 | 5 |
| E1005 | Neha Kapoor | Human Resources | 25 | 8 | 12 |

Try **E1002** or **E1004** with a 5-day trip to see a warning that the leave is not enough.

---

## 4. Configuration

All settings live in `travel_planner/config.py`. These can be changed with environment variables
(in `.env` locally, or in Render's **Environment** tab):

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `OPENAI_API_KEY` | **Yes** | — | OpenAI API key |
| `MODEL_NAME` | No | `gpt-4o-mini` | OpenAI model used by all agents |
| `AGENT_DEBUG` | No | `false` | `true` prints every internal agent step |
| `CHATBOT_PORT` | No | `7860` | Local chatbot port |
| `PORT` | Set by Render | — | When present, the chatbot listens on `0.0.0.0:$PORT` |
| `PYTHON_VERSION` | Render only | — | Python version for the Render build (`3.12.12`) |

---

## 5. Project structure

```
a2a_travel_planner_modular/
├── run_chatbot.py              Entry point: browser chatbot (used by Render)
├── run_cli.py                  Entry point: one plan in the terminal
├── run_agents.py               Entry point: start the four agents only
├── pyproject.toml / uv.lock    Dependencies for uv (exact versions)
├── requirements.txt            Same dependencies for pip / Render
├── render.yaml                 Render Blueprint
├── .python-version             Python version (3.12.12)
├── .env.example                Template for .env (your API key)
├── docs/                       Project documents (see section 7)
├── examples/                   Scripts that demonstrate single parts of the system
└── travel_planner/
    ├── config.py               All settings: model, ports, timeouts, paths
    ├── llm.py                  OpenAI clients + API key check
    ├── a2a/                    A2A protocol: models, server factory, client, server runner
    ├── agents/                 The four agents + launcher
    │   ├── hr_agent.py             :8004
    │   ├── destination_agent.py    :8001
    │   ├── weather_agent.py        :8002
    │   └── budget_agent.py         :8003
    ├── tools/                  One LangChain tool per file (leave, Wikipedia, weather, cost)
    ├── data/                   Offline cost table + synthetic SQLite leave database
    ├── orchestrator/           LangGraph state, graph, and one file per workflow step
    ├── reporting/              Audit table and flow diagram
    └── chatbot/app.py          Gradio chat interface
```

---

## 6. Troubleshooting

| Problem | Fix |
|---|---|
| `OpenAI API key check failed` | The message gives the reason: wrong key, no credit, or no internet. Check `.env` locally, or the `OPENAI_API_KEY` variable on Render. |
| `Port 8001 is used by another program` | Another copy of the app is still running. Stop it (`Ctrl+C`) and start again. |
| Local port 7860 is busy | Add `CHATBOT_PORT=7861` to `.env`. |
| Render build fails on Python version | Make sure `PYTHON_VERSION` is `3.12.12` and **Root Directory** is `a2a_travel_planner_modular`. |
| Render: `requirements.txt` not found | **Root Directory** must be `a2a_travel_planner_modular`. |
| Render: service restarts with *out of memory* | Change the instance type from `Free` to `Starter`. |
| Render: first page load is slow | Free services sleep when idle; wait about a minute for them to wake. |
| Destination section says Wikipedia failed | Temporary Wikipedia problem; the plan is still written from the model's own knowledge. |

---

## 7. Documentation

| Document | Contents |
|---|---|
| [docs/UserSystemInteraction.md](docs/UserSystemInteraction.md) | Problem statement, users, scenarios, inputs and outputs |
| [docs/AgentSpecificationDocument.md](docs/AgentSpecificationDocument.md) | Architecture, the four agents, workflow, state and error handling |
| [docs/General_Instructions.md](docs/General_Instructions.md) | Technology stack, coding standards, setup, security |
