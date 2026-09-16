# Goal

Help an employee plan a vacation and confirm, in the same answer, whether they have enough leave for it.

The user types one request in plain English, for example *"Plan a 5-day trip to Tokyo for employee E1001"*. The system researches the destination, checks the weather, estimates the cost, looks up the employee's leave balance in the HR database, and returns a single travel plan that ends with the leave position. If the user leaves something out, the system asks for that one missing detail instead of guessing.

> **Note:** This document defines the **WHAT** from a user's perspective (problem statement, scenarios, constraints). For technical architecture, see **AgentSpecificationDocument.md**. For implementation guidelines, see **General_Instructions.md**.

# User Persona

**Primary user — an employee planning personal leave.**

- Works in any department; not a developer.
- Uses a web browser and writes requests in everyday English.
- Knows their own employee ID (format `E` + digits, for example `E1001`).
- Wants one answer that covers the trip and the leave, instead of checking a travel site and an HR portal separately.
- Does not want to learn commands, fill in forms, or read technical output.

**Secondary user — a reviewer or trainer.** Runs the same system from the terminal to inspect each step: which agent was called, how long it took, and what it returned.

# Constraints

- An OpenAI API key is required (`OPENAI_API_KEY` in the `.env` file). Every request uses paid model calls; a full plan costs a fraction of a cent on `gpt-4o-mini`.
- An internet connection is required for the OpenAI API, Wikipedia and the wttr.in weather service.
- The HR database is **synthetic**: five sample employees (E1001–E1005) in a local SQLite file. Any other ID is reported as not found.
- The travel cost table is offline and covers 10 cities; other cities receive a global average.
- Everything runs as one application: four agents on internal ports 8001–8004, and the chatbot on port 7860 locally or on the port provided by the hosting platform (for example Render).
- The system **plans** a trip; it does not book flights, hotels or leave. It does not deduct leave from the database.
- Requests and answers are in English.
- Conversations are not saved. Closing the browser tab discards the chat.
- Each request is planned from scratch; the system keeps context only until a plan is delivered.

# Success Criteria

- The destination, trip length and employee ID are correctly taken from the user's message, including from a follow-up answer.
- If the destination or employee ID is missing, the system asks **only** for what is missing and remembers what was already given.
- An employee ID that is not in the HR database is detected **before** any trip research begins, and the user is asked for a valid ID.
- The final plan contains all seven sections: highlights, itinerary, weather and packing, budget, attractions, tips, and leave balance.
- The leave figures in the plan match the HR database exactly, and the plan states clearly whether the annual leave covers the trip.
- If the leave is not enough, the plan says so at the top, not only at the end.
- A complete plan is delivered in about 20–30 seconds.
- If one specialist agent is unavailable, the plan is still produced from the remaining agents, with a note about the missing part.

# Input Requirements

**Required Inputs:**

- **Travel request (free text).** Must contain a destination, for example *"Plan a 5-day trip to Tokyo"* or *"I want to visit Bali for 7 days"*.
- **Employee ID.** Format `E` followed by digits, for example `E1001`. It can be supplied in three ways:
  1. written in the message (*"…for employee E1002"*);
  2. answered when the chatbot asks for it;
  3. passed on the command line with `--employee-id E1002`.

**Optional Inputs:**

- **Trip length.** If not given, the system uses 3 days and shows that assumption in its reply.
- **`--diagram` (terminal only).** Also saves a PNG diagram of the flow and the time each step took.

**Input Validation:**

- A message with no destination and no employee ID gets one question asking for both.
- A message with a destination but no employee ID gets a question asking only for the ID, and the destination is remembered.
- If several employee IDs appear across the conversation, the most recent one is used.
- An employee ID that is not in the HR database is rejected with the list of valid IDs, and the user is asked to send a valid one. No trip research is performed.
- An empty message receives a short prompt to type a travel request.

# Output Specifications

**Primary Output — the travel plan.** A formatted document shown in the chat, containing:

1. 🌟 Trip highlights and why visit
2. 📅 Day-by-day itinerary
3. 🌤️ Weather advisory and packing tips
4. 💰 Budget breakdown and money-saving tips
5. 🎯 Must-see attractions and hidden gems
6. 💡 Essential travel tips
7. 🗓️ Leave balance — annual, casual and sick leave, whether the annual leave covers the trip, and how many days remain afterwards

If the leave does not cover the trip, a warning also appears at the top of the plan.

**Secondary Outputs:**

- **Progress messages** while the plan is being built (see *User Feedback Mechanisms*).
- **Trace footer** under each plan, listing every step and its duration, for example `check_leave_balance → A2A :8004 (2.43s)`.
- **Terminal extras:** an audit table of completed requests, and an optional PNG diagram in `outputs/`.

**Output Format:** Markdown rendered in the browser chat, or plain text in the terminal. The PNG diagram is a standard image file.

# Sample Scenarios

## Happy Path

**User:**
*"Plan a 5-day trip to Tokyo for employee E1001"*

**System:**
- Reads the request and finds destination Tokyo, duration 5 days, employee E1001.
- Asks the HR Leave Agent for E1001's leave balance and confirms the ID exists.
- Asks the Destination Research Agent about Tokyo.
- Asks the Weather Intelligence Agent for current conditions.
- Asks the Budget Estimator Agent for a 5-day cost estimate.
- Combines all four answers into one plan.

**Expected Outcome:** In about 25 seconds the user receives a complete Tokyo plan. The leave section shows 18 days of annual leave, confirms that 5 days are covered, and notes that 13 days will remain.

## Missing Employee ID (follow-up question)

**User:**
*"I want to visit Bali for 7 days"*

**System:**
- Finds the destination and duration, but no employee ID.
- Stops before contacting any agent and asks only for the ID: *"Got it — 7 days in Bali. What's your employee ID (e.g. E1001)?"*
- The user replies *"E1002"*.
- Combines the reply with the earlier message and runs the full pipeline.

**Expected Outcome:** The user only has to supply the missing detail. The Bali plan follows, with a note that E1002's 4 days of annual leave do not cover a 7-day trip.

## Leave Balance Too Low

**User:**
*"Plan a 5-day trip to Singapore for employee E1002"*

**System:**
- Retrieves E1002's balance: 4 days of annual leave.
- Continues with the destination, weather and budget agents.
- Writes the plan with a warning at the top and the full figures in the leave section.

**Expected Outcome:** A complete plan that states plainly that 4 days of annual leave do not cover the 5-day trip, and suggests shortening the trip or using another leave type.

## Error Scenarios

### Unknown Employee ID

**User:**
*"I want to visit Bali for 7 days"*, then *"E17071"*

**System:**
- Looks up E17071 in the HR database and finds nothing.
- Stops immediately, before any trip research, so the user does not wait 30 seconds for a plan that cannot be completed.
- Replies: *"⚠️ No employee found with ID 'E17071'. Valid employee IDs: E1001, E1002, E1003, E1004, E1005. Please send a valid employee ID."*
- The user sends a valid ID, and the original Bali request continues.

**Expected Outcome:** A clear message naming the rejected ID and listing valid ones, with no loss of the trip details already given.

### A Specialist Agent Is Unavailable

**User:**
*"Plan a 4-day trip to Amsterdam for employee E1003"* while the weather service is unreachable.

**System:**
- Records a warning that the weather agent could not be reached and notes which one failed.
- Continues with the remaining agents.
- Writes the plan from the information it does have.

**Expected Outcome:** A usable plan with the weather section marked as unavailable, instead of an error page.

### Non-Travel Message

**User:**
*"hello"*

**System:**
- Finds no destination and no employee ID.
- Contacts no agents and spends no time on research.

**Expected Outcome:** *"I'm a travel planner 🌍 — where would you like to go, for how long, and what's your employee ID? (e.g. 5 days in Tokyo, employee E1001)"*

# User Feedback Mechanisms

- **Live progress in the reply bubble.** Each finished step is ticked off and the current step is named, for example *"✅ Understood the request / ✅ Leave balance checked / **🔎 Researching the destination (Destination Research Agent · A2A :8001)…**"*. The user always knows which agent is working.
- **Questions instead of guesses.** Missing or invalid details produce a short question naming exactly what is needed.
- **Trace footer.** Each plan ends with the list of steps and their durations, so the user can see where the time went.
- **Terminal log.** Reviewers running the system see a timestamped line per step, including any agent warnings.
- **Startup checks.** Before the chatbot opens, the API key is verified with one small call and all four agents are confirmed ready; failures are reported in plain language.

# Performance Expectations

Measured on a laptop with `gpt-4o-mini`:

- **Response Time:** the first progress message appears in under 2 seconds.
- **Processing Time:** 20–30 seconds for a complete plan. Typical steps: leave check 2–3 s, destination research 7–9 s, weather 4–5 s, budget 4–5 s, final writing 7–10 s.
- **Short-circuit replies:** a question about missing details or an unknown ID arrives in 1–2 seconds, because no research is done.
- **Timeout:** each model call times out after 60 seconds; agent startup must complete within 20 seconds.
- **Concurrent Users:** up to 4 requests are planned at the same time. This is a single-machine demonstration, not a production deployment.

# Edge Cases

- **Several employee IDs in one conversation** (a typo then a correction): the most recent ID is used.
- **Employee with no leave left** (E1004, 0 days): a full plan is produced, stating clearly that no annual leave is available.
- **City not in the cost table:** the budget uses a global average and the plan says so.
- **Wikipedia unavailable or rate-limited:** the destination agent reports the problem as text and still writes an overview from the model's own knowledge.
- **No trip length given:** 3 days is assumed and stated back to the user.
- **New request after a plan:** the previous context is cleared, so a follow-up such as *"make it cheaper"* is treated as a new request and the system asks for the destination again.
- **Empty or whitespace-only message:** a short prompt to type a travel request; no model call is made.
- **Agent ports already in use** (for example an older copy still running): startup stops with a message naming the port, rather than failing silently.
