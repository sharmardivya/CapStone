# General Instructions

Implementation guidelines, technology stack, coding standards and development constraints for the A2A Travel Planner.

> **Note:** This document specifies the **HOW TO BUILD** (technology stack, frameworks, coding standards). For problem specification, see **UserSystemInteraction.md**. For solution architecture, see **AgentSpecificationDocument.md**.

# Technology Stack

## Programming Language

- **Language:** Python
- **Version Requirements:** Python 3.12 or later (`requires-python = ">=3.12"`). Developed and tested on 3.12.12, pinned in `.python-version`.

## Core Frameworks

- **LangGraph 1.2.5:** the orchestrator — a `StateGraph` of six nodes with conditional routing.
- **LangChain 1.3.9:** the agents — `create_agent` builds a tool-using agent for each specialist; LCEL chains handle request parsing and plan writing.
- **LangChain OpenAI 1.3.2:** the `ChatOpenAI` model client.
- **FastAPI 0.121.2:** the HTTP layer of each A2A agent, serving the AgentCard and the JSON-RPC endpoint.
- **Uvicorn 0.38.0:** the ASGI server running each agent in a background thread.
- **Gradio 6.15.1:** the browser chatbot.
- **Pydantic 2.12.5:** A2A protocol models and validation.

## AI/ML Services

- **LLM Provider:** OpenAI.
- **Primary Model:** `gpt-4o-mini` — used by all four agents and by the orchestrator. Chosen for low cost and fast replies; a full plan costs a fraction of a cent.
- **Secondary Model:** none. The model name is configurable through the `MODEL_NAME` environment variable.
- **API Configuration:** temperature 0 for the specialist agents (factual answers) and 0.3 for parsing and plan writing (natural wording); 60-second timeout per call; 2 automatic retries with exponential backoff; each agent holds its own client and connection pool.

## External Libraries

- **httpx 0.28.1:** all HTTP calls — A2A requests, Wikipedia and the weather API.
- **python-dotenv 1.2.2:** loads the API key from `.env`.
- **sqlite3 (standard library):** the HR leave database.
- **pandas 2.2.2:** formats the task audit table.
- **matplotlib 3.10.3:** draws the architecture and timing diagram.
- **a2a-sdk 0.2.5:** installed for reference; the project uses its own lightweight Pydantic models for the A2A message format.

**External APIs (no key required):** the Wikipedia API (called with a descriptive `User-Agent`, because generic clients receive HTTP 429) and `wttr.in` for weather.

## Development Tools

- **Package Manager:** `uv` (0.12.9). `pyproject.toml` declares dependencies and `uv.lock` pins exact versions.
- **Environment Management:** `uv sync` creates and maintains `.venv`; `uv run` executes commands inside it, so no manual activation is needed.
- **Code Quality Tools:** Python type hints throughout; module and function docstrings in every file. No linter is enforced.
- **Testing Framework:** none configured. Verification is done with the scripts in `examples/` and end-to-end runs (see *Testing Requirements*).

# Implementation Guidelines

## Code Structure

One responsibility per file; each agent, tool and workflow step has its own module.

**Project Structure:**
```
a2a_travel_planner_modular/
├── run_chatbot.py                  # Entry point: browser chatbot
├── run_cli.py                      # Entry point: one plan in the terminal
├── run_agents.py                   # Entry point: start the agents only
├── .env / .env.example             # API key
├── docs/                           # Project documents
├── examples/                       # Demonstration scripts
│   ├── discover_agents.py
│   ├── test_agents.py
│   ├── inspect_state.py
│   └── inspect_protocol.py
├── outputs/                        # Generated diagrams
└── travel_planner/
    ├── config.py                   # All settings: model, ports, timeouts, paths
    ├── llm.py                      # Model clients + API key check
    ├── a2a/                        # Protocol layer (no travel logic)
    │   ├── models.py               # AgentCard, Message, JSON-RPC models
    │   ├── server.py               # create_a2a_app(): handler → A2A service
    │   ├── client.py               # A2AClient: discover() and send()
    │   └── server_runner.py        # Run a service in a background thread
    ├── tools/                      # One tool per file
    │   ├── wikipedia_tool.py
    │   ├── weather_tool.py
    │   ├── cost_tool.py
    │   └── leave_tool.py
    ├── data/
    │   ├── cost_db.py              # Offline cost table
    │   └── leave_db.py             # Synthetic SQLite leave database
    ├── agents/                     # One agent per file
    │   ├── destination_agent.py    # :8001
    │   ├── weather_agent.py        # :8002
    │   ├── budget_agent.py         # :8003
    │   ├── hr_agent.py             # :8004
    │   ├── agent_runner.py         # Shared helper
    │   └── launcher.py             # Start all agents, wait until ready
    ├── orchestrator/
    │   ├── state.py                # TravelState
    │   ├── audit_log.py            # Record of completed tasks
    │   ├── graph.py                # Graph definition and plan_trip()
    │   └── nodes/                  # One file per workflow step
    ├── reporting/
    │   ├── audit_report.py
    │   └── flow_diagram.py
    └── chatbot/
        └── app.py                  # Gradio interface
```

**Naming Conventions:**
- `snake_case` for files, functions and variables; `PascalCase` for classes; `UPPER_CASE` for constants.
- Agent modules end in `_agent.py`; each exposes `AGENT_CARD`, `SYSTEM_PROMPT` and `build_<name>_app()`.
- Workflow steps are named after the action and end in `_node`, for example `check_leave_balance_node`.
- Names describe the job, not the pattern: `lookup_leave_balance`, not `tool_1`.
- A leading underscore marks internal helpers, for example `_find_employee_id`.

## Framework-Specific Guidelines

### LangGraph Guidelines

- Define the shared state as a `TypedDict`; annotate accumulating fields with `operator.add`.
- Each node is an async function taking the state and returning a dictionary of **changed fields only**.
- Express branching with `add_conditional_edges` and a small router function, never with `if` statements hidden inside a node.
- Follow one rule for user input: a node that needs something from the user writes its question into `final_plan`, and the router ends the workflow.
- Compile the graph once and reuse it.

### LangChain Guidelines

- Build each specialist agent with `create_agent(model, tools, system_prompt)`.
- Declare tools with the `@tool` decorator; the docstring is what the model reads, so it must state exactly what the tool does.
- Set a `recursion_limit` on every agent call, to stop runaway tool loops.
- Use LCEL chains (`prompt | model | parser`) for the fixed orchestrator steps, where no tool choice is needed.

### FastAPI / A2A Guidelines

- Never let an agent's HTTP details leak: `create_a2a_app(agent_card, handler)` wraps any async handler.
- Every agent serves its AgentCard at `/.well-known/agent.json` and accepts JSON-RPC `message/send` at `/`.
- Agents communicate only through the A2A client; no agent imports another agent's code.
- Run each agent in its own thread with its own event loop, so several can share one process.

## API Usage Guidelines

- **API Client Setup:** create model clients through `llm.py` only. Each agent gets its own client (`create_agent_llm()`); the orchestrator gets one per event loop (`get_synthesis_llm()`). **Do not share one client across event loops** — connections belong to the loop that opened them, and reuse elsewhere makes calls hang.
- **Authentication:** read `OPENAI_API_KEY` from the environment, loaded from `.env`. Never write a key in code.
- **Error Handling:** catch specific OpenAI exceptions (`AuthenticationError`, `RateLimitError`, `NotFoundError`, `APIConnectionError`) and translate them into a message that tells the user what to do.
- **Rate Limiting:** for Wikipedia, always send a descriptive `User-Agent`; generic clients are rejected with HTTP 429. For OpenAI, rely on the client's retry handling.
- **Retry Logic:** two automatic retries with exponential backoff for model calls. Public APIs are not retried; they have fallbacks instead. The start-up key check uses zero retries so a bad key is reported immediately.

## State Management

- **State Structure:** one `TypedDict` (`TravelState`) for the whole workflow, with a documented type for each field.
- **State Flow:** nodes never mutate the state object; they return the fields they changed and LangGraph merges them. The step log accumulates because of its `operator.add` annotation.
- **State Validation:** two checkpoints — after parsing (destination and employee ID present) and after the leave check (employee exists). Agent replies are always strings, so no field is left undefined, and a failed call stores a readable warning instead.

## Error Handling

- **Error Types:** missing user input; unknown employee ID; external API failure (Wikipedia, weather); OpenAI failures (key, quota, rate limit, timeout); agent unreachable; port already in use.
- **Error Propagation:** tool errors are returned to the model as text; handler errors become JSON-RPC errors; the calling node turns those into a warning stored in the state. The workflow continues wherever it usefully can.
- **Logging:** the standard `logging` module, one logger per module, configured once in `config.setup_logging()`. Third-party libraries are limited to warnings. Every workflow line carries the short task ID.
- **User-Facing Errors:** short, plain sentences with the next step, for example *"No employee found with ID 'E17071'. Valid employee IDs: … Please send a valid employee ID."* Tracebacks stay in the log.

## Code Quality Standards

- **Code Style:** PEP 8, four-space indentation, lines kept near 100 characters.
- **Documentation:** every module starts with a docstring saying what it does and how it fits the system; every public function has a one-line docstring.
- **Type Hints:** on all function signatures and the state definition.
- **Comments:** explain *why*, not *what* — for example why each agent needs its own model client. The code itself should be readable without comments.

## Testing Requirements

- **Unit Tests:** the leave database and both database-backed tools; request parsing (employee ID detection, missing-detail questions); chat memory; the cost lookup.
- **Integration Tests:** the A2A layer against an in-memory echo agent, covering success and the three JSON-RPC error codes; agent discovery; each agent called individually; the compiled graph's nodes and conditional edges.
- **Test Coverage:** no numeric target. The rule applied in this project is that every user-visible behaviour — each question, each error message, each successful path — has been exercised at least once and the result recorded.
- Tests that need agents can build the agent applications in memory and call them through `httpx.ASGITransport`, avoiding network ports.

# Constraints and Restrictions

## What NOT to Use

- Do **not** put API keys in code, notebooks or committed files; `.env` and `*.db` are in `.gitignore`.
- Do **not** call one agent directly from another agent's code; all communication goes through the A2A protocol.
- Do **not** use the `wikipedia` package or LangChain's `WikipediaQueryRun`: Wikipedia rate-limits their generic `User-Agent` with HTTP 429.
- Do **not** share one OpenAI client between event loops, and do not reuse a single global client for all agents.
- Do **not** use blocking calls inside async node or handler functions.
- Do **not** write user-facing text inside agent modules; questions to the user belong to the orchestrator.

## What to Avoid

- Avoid hard-coded ports, model names, paths and timeouts; they belong in `config.py`.
- Avoid business logic in the entry-point scripts; they should only wire things together.
- Avoid silent failures — log a warning and put something visible in the state.
- Avoid guessing on the user's behalf; ask for the missing detail instead.
- Avoid long functions: one job per function, one job per file.

# Environment Setup

## Environment Variables

**Required Variables:**
- `OPENAI_API_KEY`: OpenAI API key used by every agent and by the orchestrator.

**Optional Variables:**
- `MODEL_NAME`: model to use; defaults to `gpt-4o-mini`.
- `AGENT_DEBUG`: set to `true` to print every internal agent step; defaults to `false`.
- `CHATBOT_PORT`: port for the browser interface; defaults to `7860`.

**Configuration File:** copy `.env.example` to `.env` in the project folder and fill in the key. `.env` is never committed.

## Dependencies Installation

```bash
uv sync
```

This reads `pyproject.toml` and `uv.lock`, installs Python 3.12 if needed, creates `.venv` and installs the exact pinned versions.

## Development Environment

- **Virtual Environment:** created and managed by `uv`. Run everything with `uv run python …`; no activation step is required, which avoids the PowerShell script-execution restrictions on Windows.
- **IDE Recommendations:** Visual Studio Code or Cursor, with the `.venv` interpreter selected.
- **Extensions/Plugins:** the Python and Pylance extensions for type checking and navigation.

**Running the system:**

```bash
uv run python run_chatbot.py                                   # browser chatbot on :7860
uv run python run_cli.py "Plan a 5-day trip to Tokyo" --employee-id E1001
uv run python run_agents.py                                    # agents only
uv run python -m travel_planner.data.leave_db                  # create and print the HR database
uv run python -m examples.discover_agents                      # AgentCards (no model cost)
```

# Output Requirements

## Output Format

- **Output Directory:** `outputs/` for generated files; it is created automatically and excluded from version control.
- **Output Format:** the travel plan is Markdown shown in the chat or printed in the terminal; the audit report is a text table; the flow diagram is a PNG at 150 dpi.
- **Naming Convention:** fixed, descriptive file names in lower case, for example `a2a_langgraph_flow.png`.

## File Organization

- Generated files (diagrams, the SQLite database) never sit next to source files in the repository; they are produced at run time and ignored by git.
- The HR database lives with the module that owns it, at `travel_planner/data/hr_leave.db`, and is recreated automatically if deleted.

# Performance Considerations

## Optimization Guidelines

- Keep model calls to a minimum: one parsing call, one per agent, one for writing the plan. An unknown employee ID is answered straight from the database with no model call at all.
- Check the leave balance before research, so an invalid request costs 2–3 seconds instead of 30.
- Compile the LangGraph graph once and reuse it; create model clients once per agent.
- Import matplotlib only when a diagram is requested, since it is slow to load.
- Reuse agents that are already running rather than starting duplicates.

## Resource Limits

- **Memory:** a few hundred megabytes; the whole system runs in one or two Python processes.
- **Execution Time:** 20–30 seconds for a full plan; 60-second timeout per model call; agents must be ready within 20 seconds of start-up.
- **API Rate Limits:** OpenAI limits depend on the account; Wikipedia requires a descriptive `User-Agent`; `wttr.in` is a free service with no key and should not be called in tight loops.

# Security Guidelines

## Security Best Practices

- Never commit API keys. `.env` is listed in `.gitignore`; `.env.example` shows the format with a placeholder.
- Read all secrets from environment variables through `config.py`.
- Bind every service to `127.0.0.1`, so the agents and the chatbot are not reachable from the network.
- Verify the API key at start-up with one small call, so problems surface before any user request.
- Build all SQL with parameter placeholders, never string concatenation, which prevents SQL injection through the employee ID.

## Data Handling

- Employee data is synthetic and used for demonstration only.
- Never log API keys; the start-up check reports only the model's reply, never the key.
- Leave data is read-only: the system reports balances and never modifies the HR database.
- Conversations are not stored; chat history lives only in the browser session.

# Additional Notes

- **Why A2A:** each agent is an independent service with a published AgentCard, so it can be tested, replaced or rewritten in another framework without touching the orchestrator. The HR agent was added late in the project and needed no change to the existing three.
- **Why the orchestrator asks questions:** guessing produces confident, wrong plans. Every missing or invalid input becomes a short question, which also keeps the model's work focused.
- **Known limitation:** the destination, weather and budget steps are independent and could run in parallel to save roughly 8–10 seconds per request. They were left sequential for clarity; this is the most valuable next improvement.
- **Known limitation:** the system plans but does not book, and it does not deduct leave from the HR database.
- **Known limitation:** the cost table covers 10 cities and is static; other cities use a global average, which the plan states.
