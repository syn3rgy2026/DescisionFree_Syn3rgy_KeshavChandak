# Synergy Agent

> AI/ML Track — **SYN3RGY 3.0**

An autonomous AI agent that receives natural-language tasks and executes them step-by-step using a suite of tools (browser, shell, file system) powered by an OpenAI-compatible LLM endpoint.

---

## Quick Start

```bash
# 1. Clone & enter the project
git clone <repo-url>
cd synergy-agent

# 2. Create & activate virtual environment
python3 -m venv .venv
source .venv/bin/activate      # macOS / Linux
# .venv\Scripts\activate       # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and fill in INFERX_ENDPOINT and INFERX_API_KEY

# 5. Run
python main.py
```

---

## CLI Commands

| Command | Description |
|---|---|
| `exit` | Quit the program |
| `help` | Show available commands |
| `memory` | View persistent user memory *(coming soon)* |
| `history` | View task history *(coming soon)* |
| `<any text>` | Send a task to the agent |

---

## Project Structure

```
synergy-agent/
├── main.py               # CLI entry point (rich UI)
├── config.py             # Environment & global config
├── requirements.txt      # Python dependencies
├── .env                  # Local secrets (git-ignored)
├── .env.example          # Template for .env
├── agent/
│   ├── core_agent.py     # Agentic ReAct loop
│   ├── skill_router.py   # Tool registry & skill loader
│   ├── error_recovery.py # Error classification & retry logic
│   └── prompts/
│       └── master_prompt.md
├── tools/
│   ├── browser_tool.py   # Playwright web browsing
│   ├── file_tool.py      # Sandboxed file operations
│   ├── shell_tool.py     # Subprocess execution
│   └── human_confirm.py  # Human-in-the-loop confirmation
├── skills/               # Per-skill prompt .md files
├── memory/
│   ├── memory_manager.py # Read/write user memory & task log
│   ├── user_memory.md    # Persistent user facts
│   └── task_log.md       # Task history
└── output/               # Agent-generated artefacts
```

---

## Configuration

| Variable | Default | Description |
|---|---|---|
| `INFERX_ENDPOINT` | placeholder | LiteLLM / InferX API base URL |
| `INFERX_API_KEY` | placeholder | API key |
| `MODEL_ID` | `google/gemma-4-31B-it` | Model identifier |
| `MAX_STEPS` | `20` | Max agentic loop iterations |
| `SHELL_TIMEOUT` | `30` | Shell command timeout (seconds) |

---

## Ownership

| Module | Owner |
|---|---|
| `agent/core_agent.py`, `skill_router.py`, `error_recovery.py` | Person 1 |
| `tools/` | Person 2 |
| `skills/*.md` | Person 3 |
| `memory/memory_manager.py` | Person 4 |

---

## Contributing

1. Work only in your assigned module(s).
2. Replace every `raise NotImplementedError(...)` stub with real code.
3. Keep secrets out of commits — `.env` is git-ignored.
4. All terminal output must use **rich** for consistency.
