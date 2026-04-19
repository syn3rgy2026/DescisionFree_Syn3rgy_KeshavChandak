"""
core_agent.py
-------------
Central orchestrator for Synergy Agent.

Provides:
  1. load_master_prompt   — read master_prompt.md
  2. build_system_prompt  — combine master prompt + skill context + memory
  3. build_agent          — create a ready-to-use CodeAgent (optional Textual callbacks)
  4. run_agent            — build + run + memory log (CLI / scripts)
"""

import os
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
import config
from agent.skill_router import get_skills_for_task
from memory.memory_manager import get_memory_manager

_console = Console()
_memory = get_memory_manager()


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

    try:
        memory_ctx = _memory.build_memory_context(task)
        if memory_ctx:
            system_prompt += "\n\n# Memory Context (from past sessions)\n\n" + memory_ctx
    except Exception as e:
        _console.print(f"[dim]⚠️ Memory context load failed: {e}[/dim]")

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


def _step_callback(step_log) -> None:
    """Rich console trace for each agent step when no UI callbacks are passed."""
    step_num = getattr(step_log, "step_number", "?")
    _console.print(Rule(f"[bold blue]Step {step_num}[/bold blue]", style="blue"))

    model_output = getattr(step_log, "model_output", None)
    if model_output:
        _console.print(
            Panel(
                f"[cyan]{str(model_output).strip()}[/cyan]",
                title="[blue]💭 Thought / Code[/blue]",
                border_style="blue",
                padding=(0, 2),
            )
        )

    tool_calls = getattr(step_log, "tool_calls", None)
    if tool_calls:
        for tc in tool_calls:
            name = getattr(tc, "name", str(tc))
            args = getattr(tc, "arguments", {})
            _console.print(
                Panel(
                    f"[bold]Tool:[/bold]  [magenta]{name}[/magenta]\n"
                    f"[bold]Input:[/bold] [white]{args}[/white]",
                    title="[yellow]🔧 Tool Used[/yellow]",
                    border_style="yellow",
                    padding=(0, 2),
                )
            )

    obs = getattr(step_log, "observations", None)
    if obs and str(obs).strip():
        _console.print(
            Panel(
                f"[green]{str(obs).strip()}[/green]",
                title="[green]👁 Observation[/green]",
                border_style="green",
                padding=(0, 2),
            )
        )

    err = getattr(step_log, "error", None)
    if err:
        _console.print(f"[bold red]⚠ Error:[/bold red] {err}")


_GOOGLE_AND_CHART_IMPORTS = [
    "google",
    "google.oauth2",
    "google.oauth2.credentials",
    "google.auth",
    "google.auth.transport",
    "google.auth.transport.requests",
    "google_auth_oauthlib",
    "google_auth_oauthlib.flow",
    "googleapiclient",
    "googleapiclient.discovery",
    "googleapiclient.http",
    "json",
    "os",
    "base64",
    "mimetypes",
    "datetime",
    "time",
    "email",
    "email.mime",
    "email.mime.text",
    "email.mime.multipart",
    "matplotlib",
    "matplotlib.pyplot",
    "matplotlib.ticker",
    "PIL",
    "PIL.Image",
    "PIL.ImageDraw",
    "PIL.ImageFont",
    "requests",
    "hashlib",
    "textwrap",
    "io",
    "dotenv",
]


def build_agent(task: str, step_callbacks=None):
    """
    Create a fully configured CodeAgent for the given task.

    Args:
        task:           The user's task string (used to select skills).
        step_callbacks: Optional list of callbacks (e.g. Textual TUI). If None,
                        uses the Rich console step callback.

    Returns:
        CodeAgent: A ready-to-run agent instance.
    """
    from smolagents import CodeAgent, OpenAIServerModel

    instructions = build_system_prompt(task)

    model = OpenAIServerModel(
        model_id=config.MODEL_ID,
        api_base=config.INFERX_ENDPOINT,
        api_key=config.INFERX_API_KEY,
    )

    try:
        from tools import ALL_TOOLS

        tools = ALL_TOOLS
    except (ImportError, AttributeError):
        tools = []

    cbs = list(step_callbacks) if step_callbacks else [_step_callback]

    agent = CodeAgent(
        tools=tools,
        model=model,
        instructions=instructions,
        max_steps=config.MAX_STEPS,
        step_callbacks=cbs,
        additional_authorized_imports=_GOOGLE_AND_CHART_IMPORTS,
    )

    return agent


def run_agent(task: str) -> str:
    """
    Build an agent and execute the task in one call.
    Logs outcome to persistent memory.
    """
    agent = build_agent(task)

    try:
        result = agent.run(task)
        try:
            _memory.log_task(task=task, result=str(result), status="completed")
            _console.print("[dim]💾 Task result saved to memory.[/dim]")
        except Exception as e:
            _console.print(f"[dim]⚠️ Failed to save to memory: {e}[/dim]")
        return result

    except Exception as exc:
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
        raise


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
