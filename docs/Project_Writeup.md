# Project Write-up: A2A Travel Planner with HR Leave Agent

## 1. Problem Statement

I was given a pre-coded notebook containing a multi-agent travel planner. Three agents, communicating over the **A2A (Agent-to-Agent) protocol**, handled destination research, weather and budget, and together helped a user plan a vacation to a chosen place for a chosen number of days.

The task was to extend this solution:

- **Add a fourth, A2A-compliant HR agent** that looks up the user's leave balance.
- **Accept an employee ID** as an extra input, alongside the destination and trip length.
- **Present a complete travel plan together with the remaining leave** at the end.
- **Create a synthetic SQLite database** holding leave balances for five sample employees, keyed by employee ID.

## 2. Approach

**Step 1 — Understand and run the existing solution.** I set up the environment, ran the notebook end to end, and studied how each agent was wrapped as an A2A service: an AgentCard for discovery, and a JSON-RPC endpoint for messages.

**Step 2 — Restructure the notebook into a modular application.** A notebook is hard to extend and cannot be deployed, so I split the code into a Python package with one responsibility per file: protocol layer, agents, tools, data, workflow steps and reporting. I also added a browser chatbot built with Gradio.

**Step 3 — Add the HR Leave Agent.** I followed exactly the same pattern as the existing agents:

- a SQLite database with five sample employees and their annual, casual and sick leave;
- a LangChain tool that reads one employee's record;
- a LangChain agent wrapped as an A2A service on its own port (8004), with its own AgentCard.

The existing three agents needed no changes, which confirmed the value of the A2A design.

**Step 4 — Extend the orchestrator.** I added the employee ID to the shared LangGraph state and a new `check_leave_balance` step. The final plan now ends with a Leave Balance section, and warns at the top when the leave does not cover the trip.

**Step 5 — Improve the user experience.** Instead of guessing, the chatbot now asks only for what is missing and remembers what the user already said. The leave check runs *before* the research steps, so an unknown employee ID is caught in about 2 seconds rather than after a 30-second plan.

**Step 6 — Document and prepare for deployment.** I completed the three project templates, and made the application deployable on Render as a single web service.

## 3. Final Solution

```
User → Gradio chatbot → LangGraph orchestrator
          parse request ─(missing details)→ ask the user
          HR Leave Agent        :8004  ─(unknown employee)→ ask for a valid ID
          Destination Agent     :8001  (Wikipedia)
          Weather Agent         :8002  (wttr.in)
          Budget Agent          :8003  (offline cost table)
          write plan → travel plan + leave balance
```

A complete plan takes 20–30 seconds; follow-up questions are answered in 1–2 seconds.

## 4. My Hands-on Experience

The code ran on the first attempt only rarely. Most of my learning came from diagnosing real problems:

| Problem I faced | What was actually wrong | How I solved it |
|---|---|---|
| The virtual environment would not activate on Windows | PowerShell blocks `Activate.ps1` | Used `uv run`, which needs no activation |
| A table cell failed with "Missing optional dependency Jinja2" | pandas styling needs an extra package | Added the dependency to the project |
| The notebook output area showed "Failed to fetch dynamically imported module" | A stale editor cache after an update, not my code | Reloaded the editor window |
| The pipeline froze at the final step for minutes | One OpenAI client was shared across several threads, each with its own event loop | Gave each agent its own client, and added a 60-second timeout |
| Destination research failed with "Expecting value: line 1 column 1" | Wikipedia was rate-limiting the `wikipedia` library's generic User-Agent (HTTP 429) | Called the Wikipedia API directly with a descriptive User-Agent |
| The chatbot forgot my trip when I replied with my employee ID | Each message was treated as a new request, and the ID pattern only accepted four digits | Combined messages of the request in progress, and accepted any `E` + digits |
| Clicking an example sent it immediately, with no chance to edit | Default Gradio behaviour | Changed the setting so examples only fill the input box |
| My commits appeared under another person's name on GitHub | The computer's global Git identity belonged to someone else | Set my own identity for this repository only |
| The app worked locally but could not be deployed as-is | It listened only on `127.0.0.1:7860` and carried notebook-only packages | Listened on `0.0.0.0` and Render's `PORT`, and trimmed the dependencies |

Two lessons stood out. First, **the error message often points away from the real cause**: a JSON parsing error was really a rate limit, and a frozen pipeline was really an event-loop problem. Second, **testing each change against a real run** caught issues that reading the code alone would have missed.

## 5. New Learnings

**Agent-to-Agent (A2A) protocol**
- An agent publishes an **AgentCard** at `/.well-known/agent.json` so others can discover what it does.
- Agents exchange text through **JSON-RPC 2.0** over HTTP, so each one can use any framework internally.
- A new agent can be added without touching the existing ones.

**LangGraph orchestration**
- A typed shared state, where each step returns only the fields it changed.
- Reducers such as `operator.add` to accumulate a log across steps.
- Conditional edges to stop the workflow and ask the user a question.
- Streaming step-by-step updates to show live progress in the chatbot.

**LangChain agents**
- Building tool-using agents with `create_agent`, and writing tool descriptions the model can follow.
- Using `recursion_limit` to stop runaway tool loops.
- Choosing temperature per task: 0 for factual agents, 0.3 for natural writing.

**Designing reliable agentic systems**
- **Validate cheap things first:** checking the employee before researching saves time and API cost.
- **Degrade gracefully:** if one agent fails, the plan is still produced from the others.
- **Ask, don't guess:** a clarifying question is better than a confident but wrong plan.
- Async code has hidden rules; connections must not be shared across event loops.

**Engineering practice**
- Modular structure, clear naming and docstrings make a project far easier to extend.
- Environment management with `uv`, and exporting `requirements.txt` for deployment.
- Deploying to Render: binding to `0.0.0.0` and `$PORT`, and storing secrets in environment variables.
- Git hygiene: never committing API keys, and keeping a correct repository identity.

## 6. Future Improvements

- Run the destination, weather and budget steps **in parallel** to cut 8–10 seconds from each request.
- Connect to a **real HR system**, and let the employee apply for leave directly from the plan.
- Add **login** to the deployed chatbot, so the public URL cannot be used to spend API credit.
- Add an **automated test suite** that runs on every change.
- Remember preferences across sessions, such as budget level or travel style.

## 7. Conclusion

The project met all four requirements: an A2A-compliant HR agent, the employee ID as an input, a travel plan that ends with the leave balance, and a synthetic SQLite database of five employees. Beyond the requirements, it became a modular, documented and deployable application.

The most valuable outcome was practical understanding: how agents can be independent services, how an orchestrator coordinates them and handles missing input, and how much of real engineering lies in diagnosing problems that only appear when the system actually runs.
