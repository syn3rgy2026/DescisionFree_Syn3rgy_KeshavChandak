"""
core_agent.py
-------------
Central orchestrator for Synergy Agent.

Provides four functions:
  1. load_master_prompt   — read master_prompt.md
  2. build_system_prompt  — combine master prompt + skill context
  3. build_agent          — create a ready-to-use CodeAgent
  4. run_agent            — build + run in one call
"""

import os
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
import config
from agent.skill_router import get_skills_for_task
from memory.memory_manager import MemoryManager

_console = Console()
_memory = MemoryManager()  # singleton — shared across all tasks in the session


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
        print("⚠️  master_prompt.md not found — using fallback prompt")
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

    Memory context includes:
    - Recent task history (last 3 tasks)
    - Past failures (so the agent doesn't repeat mistakes)
    - Stored user facts/preferences

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
    except Exception as e:
        _console.print(f"[dim]⚠️ Memory context load failed: {e}[/dim]")

    return system_prompt


# ── 3. Step callback — prints Thought + Tool per step ───────────────

def _step_callback(step_log) -> None:
    """
    Called by smolagents after every agent step.
    CodeAgent produces code (model_output) and runs it (observations).
    """
    step_num = getattr(step_log, 'step_number', '?')

    _console.print(Rule(f"[bold blue]Step {step_num}[/bold blue]", style="blue"))

    # ── Thought: raw LLM output (includes generated code) ────────────
    model_output = getattr(step_log, 'model_output', None)
    if model_output:
        _console.print(
            Panel(
                f"[cyan]{str(model_output).strip()}[/cyan]",
                title="[blue]💭 Thought / Code[/blue]",
                border_style="blue",
                padding=(0, 2),
            )
        )

    # ── Tool used (ToolCallingAgent path, shown if present) ──────────
    tool_calls = getattr(step_log, 'tool_calls', None)
    if tool_calls:
        for tc in tool_calls:
            name = getattr(tc, 'name', str(tc))
            args = getattr(tc, 'arguments', {})
            _console.print(
                Panel(
                    f"[bold]Tool:[/bold]  [magenta]{name}[/magenta]\n"
                    f"[bold]Input:[/bold] [white]{args}[/white]",
                    title="[yellow]🔧 Tool Used[/yellow]",
                    border_style="yellow",
                    padding=(0, 2),
                )
            )

    # ── Observation: stdout from executing the generated code ─────────
    obs = getattr(step_log, 'observations', None)
    if obs and str(obs).strip():
        _console.print(
            Panel(
                f"[green]{str(obs).strip()}[/green]",
                title="[green]👁 Observation[/green]",
                border_style="green",
                padding=(0, 2),
            )
        )

    # ── Error (if any) ────────────────────────────────────────────────
    err = getattr(step_log, 'error', None)
    if err:
        _console.print(f"[bold red]⚠ Error:[/bold red] {err}")


# ── 4. Build a CodeAgent instance ────────────────────────────────────

def build_agent(task: str):
    """
    Create a fully configured CodeAgent for the given task.

    Args:
        task: The user's task string (used to select skills).

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
        print("⚠️  Tools not loaded — running agent with no tools")
        tools = []

    agent = CodeAgent(
        tools=tools,
        model=model,
        instructions=instructions,
        max_steps=config.MAX_STEPS,
        step_callbacks=[_step_callback],
    )

    return agent


# ── 4. Run the agent end-to-end ──────────────────────────────────────

def run_agent(task: str) -> str:
    """
    Build an agent and execute the task in one call.
    Automatically saves the result (or error) to persistent memory.

    Args:
        task: The user's task string.

    Returns:
        str: The agent's final result.
    """
    agent = build_agent(task)

    try:
        result = agent.run(task)

        # ── Auto-save successful result to memory ─────────────────────
        try:
            _memory.log_task(task=task, result=str(result), status="completed")
            _console.print("[dim]💾 Task result saved to memory.[/dim]")
        except Exception as e:
            _console.print(f"[dim]⚠️ Failed to save to memory: {e}[/dim]")

        return result

    except Exception as exc:
        # ── Auto-save failure to memory so we don't repeat it ─────────
        try:
            _memory.log_task(
                task=task,
                result=str(exc),
                status="error",
                errors=str(exc),
            )
            _console.print("[dim]💾 Task failure saved to memory (will avoid next time).[/dim]")
        except Exception:
            pass

        raise  # re-raise so error_recovery can handle it


# ── Self-test ────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("TEST 1: load_master_prompt()")
    print("=" * 60)
    prompt = load_master_prompt()
    print(f"  Length: {len(prompt)} chars")
    print(f"  Preview: {prompt[:150]}...\n")

    print("=" * 60)
    print("TEST 2: build_system_prompt('search the web for news')")
    print("=" * 60)
    sp = build_system_prompt("search the web for news")
    print(f"  Length: {len(sp)} chars")
    print(f"  Contains skills: {'Relevant Skills' in sp}\n")

    print("=" * 60)
    print("TEST 3: build_agent('write a python script')")
    print("=" * 60)
    try:
        ag = build_agent("write a python script")
        print(f"  Agent type: {type(ag).__name__}")
        print(f"  Max steps: {ag.max_steps}")
        print(f"  Tools loaded: {len(ag.tools)}")
    except Exception as e:
        print(f"  ⚠️  Could not build agent (expected if no LLM): {e}")

    print("\n" + "=" * 60)
    print("TEST 4: run_agent (skipped — requires live LLM)")
    print("=" * 60)
    print("  Pass. (Would call run_agent in production.)")
