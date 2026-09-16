# CapStone

This project uses [uv](https://docs.astral.sh/uv/) to manage Python and packages. You never need to run `Activate.ps1`: uv and VS Code both use the `.venv` folder directly.

## One-time setup

1. **Install uv** (skip this if `uv --version` already works):
   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```
   Close and reopen your terminal and VS Code afterwards so the new PATH takes effect.

2. **Install everything.** From the repo root (`C:\Divya\code\CapStone`):
   ```powershell
   uv sync
   ```
   This installs Python 3.12 if needed (see `.python-version`), creates `.venv`, and installs the exact package versions from `uv.lock`.

3. **Add your OpenAI key.** Create `Capstone_Project_Sep26/a2a_langgraph_travel_planner/.env` containing:
   ```
   OPENAI_API_KEY=sk-...
   ```
   `.env` is listed in `.gitignore`, so git won't commit it.

## Run the notebooks in VS Code

1. Open the `C:\Divya\code\CapStone` folder in VS Code.
2. Open a notebook from `Capstone_Project_Sep26/a2a_langgraph_travel_planner/`:
   - `a2a_langgraph_travel_planner.ipynb`: LangGraph pipeline plus three A2A agents on ports 8001–8003.
   - `mcp_langgraph_travel_agent.ipynb`: ReAct agent plus an MCP tool server on port 8011.
3. Click **Select Kernel** (top right), then **Python Environments**, then **.venv (Python 3.12.12)**.
4. Click **Run All**.

Skip the commented-out `%pip install` cells; `uv sync` already installed those packages.

Notes:
- **Before running a notebook a second time, click Restart Kernel.** Otherwise the servers from the first run are still using ports 8001–8003.
- **The last cell of the MCP notebook waits for typed input.** Type `quit` to stop it.

## Run from the terminal (optional)

Prefix any command with `uv run` to use `.venv` without activating it:
```powershell
uv run python some_script.py
uv run --with jupyter jupyter lab   # opens the notebooks in the browser
```

## Adding or updating packages

```powershell
uv add <package>        # adds to pyproject.toml and uv.lock, installs into .venv
uv remove <package>
```
Commit `pyproject.toml` and `uv.lock` so anyone can recreate the same environment with `uv sync`.
