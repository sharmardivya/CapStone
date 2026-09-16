# Goal

Build a travel planning system in which four independent AI agents each own one subject — destination research, weather, budget and HR leave — and a LangGraph orchestrator calls them in turn and merges their answers into one plan.

Each agent runs as its own web service and is reached over the **A2A (Agent-to-Agent) protocol**, using JSON-RPC 2.0 over HTTP. The orchestrator never sees inside an agent: it sends text and receives text. This keeps agents replaceable, independently testable, and free to use a different framework internally without affecting the rest of the system.

> **Note:** This document focuses on the **WHAT** (agents, responsibilities, workflow) and **HOW** (architecture, interactions). For implementation guidelines, technology stack, and coding standards, refer to **General_Instructions.md**.

# System Architecture Overview

The system has three layers:

1. **User interface** — a Gradio chatbot in the browser, or a command-line script.
2. **Orchestrator** — a LangGraph state machine of six steps that decides what to do next and asks the user when something is missing.
3. **Specialist agents** — four A2A services, each a LangChain agent with one tool, running on ports 8001–8004.

```
Browser chatbot (Gradio, :7860)  /  Terminal (run_cli.py)
                    │
                    ▼
        LangGraph orchestrator (6 nodes, shared TravelState)
                    │  A2A: JSON-RPC 2.0 over HTTP
     ┌──────────────┼───────────────┬──────────────────┐
     ▼              ▼               ▼                  ▼
HR Leave      Destination      Weather            Budget
Agent :8004   Research :8001   Intelligence :8002  Estimator :8003
SQLite        Wikipedia API    wttr.in API        Offline cost table
```

**Architecture Pattern:** Sequential pipeline with two conditional exits. The orchestrator stops early and asks the user when the request is incomplete or the employee ID is unknown.

**State Management:** A single shared state object (`TravelState`, a `TypedDict`) flows through the nodes. Each node returns only the fields it changed. The step log is annotated with `operator.add`, so entries accumulate instead of overwriting each other.

**Orchestration:** LangGraph `StateGraph`. Fixed edges define the normal order; conditional edges implement the two early exits. Agents never call each other, so there is one clear place where the order is decided.

**Discovery:** Every agent publishes an **AgentCard** at `/.well-known/agent.json`, giving its name, URL and skills. The orchestrator uses this both to discover agents and to confirm they are ready before work is sent.

# Agents

## HRLeaveAgent

### Goal

Report an employee's remaining leave and state whether it covers the planned trip.

### Responsibilities

* Look up the employee's record in the HR database by employee ID.
* Report annual, casual and sick leave balances without altering them.
* Compare annual leave against the trip length (one leave day per trip day) and state how many days would remain.
* Identify unknown employee IDs so the orchestrator can ask the user for a valid one.

### Input

**Format:** Plain text inside an A2A JSON-RPC `message/send` request.
**Source:** The orchestrator's `check_leave_balance` node.
**Required Fields:** message text containing the employee ID and the trip.
**Optional Fields:** `context` object carrying `task_id` and the caller's name, used for logging.
**Validation:** The agent extracts the employee ID with the shared pattern `\bE\d+\b` and looks it up in SQLite before doing anything else.
**Example:**
```
"Leave balance for employee E1002. Planned trip: 5 days in Singapore."
```

### Output

**Format:** Plain text in the A2A reply message.
**Destination:** Stored in `leave_info` in the shared state; later used by the plan writer.
**Fields:** employee name, annual/casual/sick balances, whether the trip is covered, days remaining.
**Validation:** Balances come only from the database; the prompt forbids inventing figures. Replies for unknown IDs always begin with the agreed marker text `No employee found with ID`.
**Example:**
```
Rahul Mehta (E1002, Finance) has 4 days of annual leave, 2 casual and 8 sick.
The 5-day trip is NOT covered: 4 days of annual leave would leave 0 days and
still fall 1 day short.
```

### Dependencies

**Prerequisites:**
- `parse_query` must have found an employee ID.
- The SQLite file `travel_planner/data/hr_leave.db` must exist; it is created automatically at agent start-up.

**Dependent Agents:** None. Its result gates the rest of the pipeline: an unknown ID stops the workflow.

### Tools

* `lookup_leave_balance` — a LangChain tool that reads one row from SQLite by employee ID.
* `sqlite3` (Python standard library) — database access; one connection per call, closed immediately.
* `ChatOpenAI` — writes the comparison in readable English.

**Tool Configuration:**
- Model `gpt-4o-mini`, temperature 0, 60-second timeout.
- Database path from `config.LEAVE_DB_PATH`.
- Maximum 6 agent steps per request.

### Preconditions

- The agent's HTTP server answers on port 8004 and serves its AgentCard.
- `OPENAI_API_KEY` is present and valid (checked once at start-up).

### Postconditions

- `leave_info` in the shared state holds the leave summary.
- If the employee ID is unknown, the state also holds a question for the user and the workflow ends.
- The HR database is unchanged: this agent only reads.

### Error Handling

**Possible Errors:**
- *Unknown or missing employee ID* — answered directly from the database, with no model call, listing the valid IDs.
- *Model or network failure* — caught and returned as a short message so the pipeline continues.
- *Database file missing* — prevented by creating the database when the agent starts.

**Error Recovery:**
- Unknown IDs are a normal outcome, not a failure: the orchestrator turns them into a question for the user.
- If the agent cannot be reached at all, the calling node records a warning and the plan is written without the leave section.

**Error Output:** Handler failures become JSON-RPC error responses (code `-32603`); everything else is readable text in the reply.

### Retry Logic

- **Max Retries:** 2, applied by the OpenAI client to model calls only.
- **Retry Conditions:** temporary network errors and rate limits.
- **Backoff Strategy:** the OpenAI client's built-in exponential backoff. Database reads are local and are not retried.

### Performance Considerations

- **Expected Execution Time:** 2–3 seconds; unknown IDs return in well under a second because no model call is made.
- **Timeout:** 60 seconds per model call; 60 seconds for the whole A2A request.
- **Resource Usage:** one model call per request; a database read of a few kilobytes.

### Side Effects

- Creates the SQLite database with five sample employees if it does not exist.
- Writes log lines. It never modifies leave balances.

## DestinationResearchAgent

### Goal

Produce a factual overview of the destination: attractions, culture, history and practical visitor tips.

### Responsibilities

* Search Wikipedia for the destination and read the introductions of the best-matching articles.
* Turn those facts into a clear overview for a traveller.
* Continue usefully when Wikipedia is unavailable, rather than failing the request.

### Input

**Format:** Plain text in an A2A `message/send` request.
**Source:** The orchestrator's `research_destination` node.
**Required Fields:** message text naming the destination.
**Optional Fields:** `context` with `task_id`.
**Validation:** Empty or unknown places are handled by the tool, which reports that no article was found.
**Example:**
```
"Research destination: Tokyo"
```

### Output

**Format:** Plain text (several paragraphs).
**Destination:** `destination_info` in the shared state.
**Fields:** free-form overview; typically 3,000–4,000 characters.
**Validation:** Facts come from Wikipedia article text passed to the model; tool failures are passed through as visible text.
**Example:**
```
Tokyo is the capital and most populous city of Japan … Key attractions include
Senso-ji temple in Asakusa, the Meiji Shrine … Visitors should note that …
```

### Dependencies

**Prerequisites:** `parse_query` must have found a destination; the leave check must have passed.

**Dependent Agents:** None directly. The plan writer uses its output.

### Tools

* `search_wikipedia` — a LangChain tool that queries the Wikipedia API over HTTPS with `httpx`.
* `ChatOpenAI` — writes the overview.

**Tool Configuration:**
- Wikipedia API with a descriptive `User-Agent`; generic clients are rate-limited with HTTP 429.
- Top 2 articles, 1,500 characters of each.
- 15-second HTTP timeout; maximum 8 agent steps.

### Preconditions

- The agent answers on port 8001.
- Outbound HTTPS access to `en.wikipedia.org`.

### Postconditions

- `destination_info` holds the overview, or a clearly marked note that research was unavailable.

### Error Handling

**Possible Errors:**
- *Wikipedia unreachable or rate-limited* — the tool returns the problem as text, and the model still writes an overview from what it knows.
- *No matching article* — the tool says so explicitly.
- *Model failure* — falls back to a plain Wikipedia summary with no model involved.

**Error Recovery:** Two levels of fallback: tool failure is handled by the model, and model failure is handled by the direct Wikipedia summary.

**Error Output:** A note inside the text, so it appears in the plan and in the logs.

### Retry Logic

- **Max Retries:** 2 for model calls (OpenAI client default). Wikipedia calls are not retried; the fallback path covers them.
- **Retry Conditions:** temporary network errors, rate limits.
- **Backoff Strategy:** exponential backoff in the OpenAI client.

### Performance Considerations

- **Expected Execution Time:** 7–9 seconds, the slowest agent because it reads and summarises the most text.
- **Timeout:** 15 seconds for Wikipedia; 60 seconds per model call.
- **Resource Usage:** 1–2 model calls and 1 Wikipedia request per trip.

### Side Effects

None beyond logging. It only reads public data.

## WeatherIntelligenceAgent

### Goal

Report current conditions at the destination and turn them into packing and activity advice.

### Responsibilities

* Fetch live weather for the destination city.
* Summarise temperature, humidity, wind and conditions in plain language.
* Give practical advice, such as what to pack and when to plan outdoor activities.

### Input

**Format:** Plain text in an A2A `message/send` request.
**Source:** The orchestrator's `check_weather` node.
**Required Fields:** message text naming the city.
**Optional Fields:** `context` with `task_id`.
**Validation:** The weather service's response code is checked before the data is read.
**Example:**
```
"Weather for Tokyo"
```

### Output

**Format:** Plain text.
**Destination:** `weather_info` in the shared state.
**Fields:** temperature, feels-like, humidity, wind, visibility, conditions, plus advice.
**Validation:** Figures come only from the weather service; failures are reported as text.
**Example:**
```
Tokyo, Japan: 24°C (feels like 25°C), humidity 61%, wind 11 km/h, partly cloudy.
Pack light layers and a compact umbrella …
```

### Dependencies

**Prerequisites:** a destination in the state; the leave check must have passed.

**Dependent Agents:** None directly; the plan writer uses its output.

### Tools

* `fetch_weather_data` — a LangChain tool calling the free `wttr.in` JSON API with `httpx`.
* `ChatOpenAI` — writes the summary and advice.

**Tool Configuration:** no API key required; 12-second HTTP timeout; maximum 6 agent steps.

### Preconditions

- The agent answers on port 8002.
- Outbound HTTPS access to `wttr.in`.

### Postconditions

- `weather_info` holds the summary, or a note that weather data was unavailable.

### Error Handling

**Possible Errors:**
- *Weather service down, slow or returning an error code* — the tool returns a short explanation as text.
- *Unrecognised city* — reported as unavailable data for that name.
- *Model failure* — the handler returns a brief "weather unavailable" message.

**Error Recovery:** Weather is optional to the plan: the pipeline always continues and the plan notes what is missing.

**Error Output:** Text inside the reply, plus a warning in the log.

### Retry Logic

- **Max Retries:** 2 for model calls; the weather call is not retried.
- **Retry Conditions:** temporary network errors and rate limits.
- **Backoff Strategy:** exponential backoff in the OpenAI client.

### Performance Considerations

- **Expected Execution Time:** 4–5 seconds.
- **Timeout:** 12 seconds for the weather API; 60 seconds per model call.
- **Resource Usage:** one weather request and 1–2 model calls per trip.

### Side Effects

None beyond logging.

## BudgetEstimatorAgent

### Goal

Produce an itemised cost estimate for the trip, with the local currency and money-saving advice.

### Responsibilities

* Look up daily costs (hotel, food, transport, activities) for the destination.
* Multiply by the trip length and show the daily and total figures.
* Convert to the local currency using the stored exchange rate.
* State clearly when a city is not in the table and a global average was used.

### Input

**Format:** Plain text in an A2A `message/send` request.
**Source:** The orchestrator's `estimate_budget` node.
**Required Fields:** message text with the trip length and destination.
**Optional Fields:** `context` with `task_id`.
**Validation:** City names are matched in lower case; unknown cities fall back to the `default` row.
**Example:**
```
"Budget for 5 days in Singapore"
```

### Output

**Format:** Plain text, usually including a small table.
**Destination:** `budget_info` in the shared state.
**Fields:** per-item daily costs, daily total, trip total, currency, exchange rate, savings tips.
**Validation:** All figures come from the offline table; the prompt requires the tool to be used.
**Example:**
```
Singapore (exact city data): hotel $140/day, food $55, transport $20,
activities $40 → $255/day, $1,275 for 5 days (≈ S$1,709 at 1 USD = 1.34 SGD).
```

### Dependencies

**Prerequisites:** destination and duration in the state; the leave check must have passed.

**Dependent Agents:** None directly; the plan writer uses its output.

### Tools

* `lookup_travel_costs` — a LangChain tool reading the offline `COST_DB` table (10 cities plus a default row).
* `ChatOpenAI` — writes the itemised budget and tips.

**Tool Configuration:** no network access; maximum 6 agent steps.

### Preconditions

- The agent answers on port 8003.

### Postconditions

- `budget_info` holds the estimate, including a note when the global average was used.

### Error Handling

**Possible Errors:**
- *City not in the table* — normal behaviour: the default row is used and labelled.
- *Model failure* — the handler returns a short "budget estimation failed" message.

**Error Recovery:** The cost lookup is local and cannot fail on the network, which makes this the most reliable agent.

**Error Output:** Text in the reply, plus a log warning.

### Retry Logic

- **Max Retries:** 2 for model calls.
- **Retry Conditions:** temporary network errors and rate limits.
- **Backoff Strategy:** exponential backoff in the OpenAI client.

### Performance Considerations

- **Expected Execution Time:** 4–5 seconds.
- **Timeout:** 60 seconds per model call.
- **Resource Usage:** 1–2 model calls; no network calls beyond OpenAI.

### Side Effects

None beyond logging.

# Workflow/Orchestration

The orchestrator is a LangGraph `StateGraph` with six nodes. Two of them are decision points where the workflow can stop and hand a question back to the user.

## Workflow Diagram

```
START
  │
  ▼
[1] parse_query ───────────────(destination or employee ID missing)──► ask user → END
  │
  ▼
[2] check_leave_balance ──A2A :8004──(employee ID not in HR database)──► ask user → END
  │
  ▼
[3] research_destination ──A2A :8001
  │
  ▼
[4] check_weather ────────A2A :8002
  │
  ▼
[5] estimate_budget ──────A2A :8003
  │
  ▼
[6] synthesize_plan  →  travel plan + leave balance  →  END
```

## Execution Flow

1. **Understand the request:** extract destination, duration and employee ID from the user's messages.
   - **Agent:** none; an LLM chain inside the orchestrator, with a regular-expression fallback.
   - **Condition:** proceed only if both destination and employee ID are known.
   - **Next Step:** the leave check, or a question to the user.

2. **Check leave first:** ask the HR Leave Agent for the balance.
   - **Agent:** HRLeaveAgent (:8004).
   - **Condition:** proceed only if the employee ID exists in the database.
   - **Next Step:** destination research, or a question asking for a valid ID.

3. **Research the destination.**
   - **Agent:** DestinationResearchAgent (:8001).
   - **Condition:** none; failures degrade to a note.
   - **Next Step:** weather.

4. **Check the weather.**
   - **Agent:** WeatherIntelligenceAgent (:8002).
   - **Condition:** none.
   - **Next Step:** budget.

5. **Estimate the budget.**
   - **Agent:** BudgetEstimatorAgent (:8003).
   - **Condition:** none.
   - **Next Step:** write the plan.

6. **Write the plan:** merge all four replies into the seven-section plan and record the task in the audit log.
   - **Agent:** none; an LLM chain inside the orchestrator.
   - **Condition:** none.
   - **Next Step:** END; the plan is returned to the user.

## Conditional Logic

The rule is uniform: **any node that needs something from the user writes its question into `final_plan`, and the router then ends the workflow.**

- **After `parse_query`:** destination and employee ID both present → `check_leave_balance`; otherwise → END with a question naming only what is missing.
- **After `check_leave_balance`:** the HR reply starts with the "no employee found" marker → END with a request for a valid ID; otherwise → `research_destination`.

Checking leave before research is deliberate: an unknown ID is caught in 2–3 seconds instead of after a 30-second plan that could not be completed.

## Parallel Execution

Not used in this version. Nodes 3, 4 and 5 are independent and could run together with `asyncio.gather`, which would cut roughly 8–10 seconds from each request. The sequential order was kept because it is easier to follow, to log and to demonstrate step by step. The four agent servers do, however, handle concurrent requests, so up to four users can be served at once.

# State Management

## State Structure

`TravelState` is a `TypedDict` passed from node to node. Each node returns only the fields it changed; returned fields replace the old values, except the log, which accumulates.

**State Fields:**
- `query`: str — the user's request; in the chatbot, the messages of the current request joined together.
- `employee_id`: str — supplied by the caller or found in the text; `""` if unknown.
- `destination`: str — city name; `""` if none was found.
- `duration`: str — for example `"5 days"`; defaults to `"3 days"`.
- `destination_info`: str — reply from the Destination Research Agent.
- `weather_info`: str — reply from the Weather Intelligence Agent.
- `budget_info`: str — reply from the Budget Estimator Agent.
- `leave_info`: str — reply from the HR Leave Agent.
- `final_plan`: str — the finished plan, or a question for the user.
- `task_id`: str — short ID linking all log lines of one request.
- `node_log`: List[str] — one line per step with its duration; annotated with `operator.add` so entries are appended, not overwritten.

## State Flow

- **parse_query** reads `query`, `employee_id`; writes `destination`, `duration`, `employee_id`, `task_id`, `node_log`, and `final_plan` if details are missing.
- **check_leave_balance** reads `employee_id`, `duration`, `destination`, `task_id`; writes `leave_info`, `node_log`, and `final_plan` if the ID is unknown.
- **research_destination** reads `destination`; writes `destination_info`, `node_log`.
- **check_weather** reads `destination`; writes `weather_info`, `node_log`.
- **estimate_budget** reads `destination`, `duration`; writes `budget_info`, `node_log`.
- **synthesize_plan** reads all information fields; writes `final_plan`, `node_log`, and one audit record.

## State Validation

- **After parsing:** destination and employee ID must both be non-empty, otherwise the workflow stops and asks.
- **After the leave check:** the reply must not be the "employee not found" marker, otherwise the workflow stops and asks.
- **At every agent call:** failures are converted into a visible warning string, so no field is ever left undefined.
- **Structural validation:** every A2A message is validated by Pydantic models on both sides, so malformed requests are rejected with a JSON-RPC error rather than causing a crash.

# Error Handling Strategy

## Error Propagation

- **Inside an agent:** tool errors are returned to the agent's own model as text, so it can still answer. Handler errors become JSON-RPC error responses.
- **Between agent and orchestrator:** the A2A client raises an error for a JSON-RPC error response; the calling node catches it, logs a warning and stores a message such as *"⚠️ The weather agent was unavailable…"*.
- **To the user:** the plan is still produced, with the missing part noted. The chatbot shows a short message only if the whole pipeline fails.

## Global Error Handler

- The chatbot wraps the pipeline: any unexpected exception is logged with its full traceback and shown to the user as one short message, so the interface never breaks.
- Start-up checks run before any request: the API key is verified with one small call, and all four agents must publish their AgentCards within 20 seconds. If a port is occupied, the error names the port and the agent.

## Recovery Mechanisms

- **Degrade rather than fail:** a missing agent removes one section from the plan; it does not stop the request.
- **Layered fallbacks:** Wikipedia failure → model knowledge; model failure → direct Wikipedia summary; plan-writing failure → the raw agent replies are shown.
- **Automatic retries:** the OpenAI client retries temporary errors twice with backoff; a 60-second timeout prevents a hung call from blocking a request.
- **Agent reuse:** agents already running are detected and reused rather than started twice.
- **Ask the user:** anything the system cannot resolve by itself — a missing destination, an unknown employee ID — becomes a plain question instead of a guess.

# Testing Considerations

## Unit Testing

- **Leave database:** creating the database twice is safe; lookups are case-insensitive; unknown IDs return nothing.
- **Leave tool:** a valid ID returns all three balances; an unknown ID returns the marker text and lists the valid IDs.
- **Cost tool:** a listed city returns exact data; an unlisted city is labelled as a global average.
- **Request parsing:** the employee ID is found in a parameter or in the text, and the latest ID wins; missing details produce the correct question.
- **Chat memory:** messages since the last finished plan are combined correctly.

## Integration Testing

- **A2A layer:** an echo agent served in memory verifies discovery, a successful call, a failing handler (error `-32603`), an unknown method (`-32601`) and malformed JSON (`-32600`).
- **Agent discovery:** `examples/discover_agents.py` confirms all four AgentCards, without using the model.
- **Individual agents:** `examples/test_agents.py` calls each agent over A2A with one sample message.
- **Graph wiring:** the compiled graph is checked for the expected six nodes and both conditional exits.

## End-to-End Testing

- **Happy path:** *"Plan a 3-day trip to Rome for employee E1003"* → a plan with all seven sections and a correct leave balance.
- **Insufficient leave:** E1002 with a 5-day trip → a warning at the top and correct figures at the end.
- **Conversation with follow-ups:** *"visit Bali for 7 days"* → asks for the ID → *"E17071"* → rejected → *"E1002"* → full plan.
- **New request after a plan:** *"hello"* → the system asks for all details again.
- **Interface check:** the chatbot page loads, progress messages stream in order, and the trace footer lists every step.
- **Reports:** the audit table and the PNG diagram are produced after a run and show the correct steps and timings.
