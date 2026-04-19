"""
core_agent.py
-------------
Central orchestrator for Synergy Agent.

Provides:
  1. load_master_prompt   — read master_prompt.md
  2. build_system_prompt  — combine master prompt + skill context + memory
  3. build_agent          — create a ready-to-use CodeAgent (no UI coupling)
"""

import os
from pathlib import Path
from rich.console import Console
import config
from agent.skill_router import get_skills_for_task
from memory.memory_manager import get_memory_manager

_console = Console()
_memory = get_memory_manager()  # singleton — shared across all tasks in the session


# ── 1. Load the master prompt ─────────────────────────────────────────

def load_master_prompt() -> str:
    """
    Read master_prompt.md from the prompts folder.

    Returns:
        str: The master prompt content.
             Falls back to a basic string if the file is missing.
    """
    filepath = os.path.join(config.PROMPTS_FOLDER, "master_prompt.md")
    if not os.path.exists(filepath):
        return (
            "You are Synergy Agent, an autonomous execution agent. "
            "Complete the user's task step-by-step using available tools. "
            "Always verify your work before finishing."
        )
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


# ── 2. Build the full system prompt ──────────────────────────────────

def build_system_prompt(task: str) -> str:
    """
    Combine the master prompt with skill context + memory context.

    Args:
        task: The user's task string.

    Returns:
        str: A complete system prompt ready for the LLM.
    """
    master = load_master_prompt()
    skills = get_skills_for_task(task)

    system_prompt = master
    if skills:
        system_prompt += "\n\n# Relevant Skills & Instructions\n\n" + skills

    # Inject past memory context so agent can learn from history
    try:
        memory_ctx = _memory.build_memory_context(task)
        if memory_ctx:
            system_prompt += "\n\n# Memory Context (from past sessions)\n\n" + memory_ctx
    except Exception:
        pass

    # Where files may go on this machine (so "save on Desktop" is not ignored)
    try:
        cwd = str(Path.cwd().resolve())
        home = str(Path.home().resolve())
        desktop = str((Path.home() / "Desktop").resolve())
        of = config.OUTPUT_FOLDER.replace("\\", "/").strip()
        if of.startswith("./"):
            of = of[2:].strip("/")
        out_abs = str((Path.cwd() / of).resolve())
        system_prompt += (
            "\n\n# Paths on this machine (follow the user's location request)\n\n"
            f"- **Working directory** (relative paths in shell code resolve here): `{cwd}`\n"
            f"- **Default artefact folder** when the user does *not* specify a location: `{out_abs}` "
            "(use a relative name like `report.md` or `output/report.md` — file tools place bare names here).\n"
            f"- **User home**: `{home}` — if they say Desktop, Documents, Downloads, or `~/...`, write using a "
            f"**full absolute path** (e.g. `{desktop}/filename.ext`). Do **not** silently use only `output/` when "
            "they asked for another folder.\n"
            "- In the final answer, list **absolute paths** for every file created or edited.\n"
        )
    except Exception:
        pass

    return system_prompt


# ── 3. Build a CodeAgent instance ────────────────────────────────────

def build_agent(task: str, step_callbacks=None):
    """
    Create a fully configured CodeAgent for the given task.

    Args:
        task:           The user's task string (used to select skills).
        step_callbacks: Optional list of callbacks. If None, no callbacks
                        are attached. The Textual TUI passes its own.

    Returns:
        CodeAgent: A ready-to-run agent instance.
    """
    from smolagents import CodeAgent, OpenAIServerModel

    instructions = build_system_prompt(task)

    # Connect to InferX-hosted model via OpenAI-compatible API
    model = OpenAIServerModel(
        model_id=config.MODEL_ID,
        api_base=config.INFERX_ENDPOINT,
        api_key=config.INFERX_API_KEY,
    )

    # Try to import project tools; fall back to empty list if not ready
    try:
        from tools import ALL_TOOLS
        tools = ALL_TOOLS
    except (ImportError, AttributeError):
        tools = []

    agent = CodeAgent(
        tools=tools,
        model=model,
        instructions=instructions,
        max_steps=config.MAX_STEPS,
        step_callbacks=step_callbacks or [],
    )

    return agent


# ── Self-test ────────────────────────────────────────────────────────
if __name__ == "__main__":
    _console.print("=" * 60)
    _console.print("TEST 1: load_master_prompt()")
    _console.print("=" * 60)
    prompt = load_master_prompt()
    _console.print(f"  Length: {len(prompt)} chars")
    _console.print(f"  Preview: {prompt[:150]}...\n")

    _console.print("=" * 60)
    _console.print("TEST 2: build_system_prompt('search the web for news')")
    _console.print("=" * 60)
    sp = build_system_prompt("search the web for news")
    _console.print(f"  Length: {len(sp)} chars")
    _console.print(f"  Contains skills: {'Relevant Skills' in sp}\n")

    _console.print("=" * 60)
    _console.print("TEST 3: build_agent('write a python script')")
    _console.print("=" * 60)
    try:
        ag = build_agent("write a python script")
        _console.print(f"  Agent type: {type(ag).__name__}")
        _console.print(f"  Max steps: {ag.max_steps}")
        _console.print(f"  Tools loaded: {len(ag.tools)}")
    except Exception as e:
        _console.print(f"  ⚠️  Could not build agent (expected if no LLM): {e}")
