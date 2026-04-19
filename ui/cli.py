"""
cli.py
------
Premium TUI (Textual User Interface) dashboard for Synergy Agent.

Uses a three-zone Layout:
  1. [Header] - Agent name, model, current task, attempts
  2. [Body]   - Scrolling step history + current thinking/tool panel
  3. [Footer] - Real-time metrics (Steps, Tokens, Clock)

All styling is built for High Contrast on both Light and Dark themes.
"""

import time
import os
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.layout import Layout
from rich.live import Live
from rich.spinner import Spinner
from rich.prompt import Prompt
from rich import box

from ui.theme import (
    PRIMARY, THINKING, TOOL, SUCCESS, ERROR, DIM, ACCENT,
    PLANNING, STEP_BORDER, INPUT_ARROW, AGENT_NAME, AGENT_VERSION,
)

_console = Console()

def _trunc(text: str, length: int = 80) -> str:
    """Truncate text with ellipsis if too long."""
    if not text: return ""
    text = str(text).replace("\n", " ").strip()
    return text[:length] + "…" if len(text) > length else text


class AgentCLI:
    """TUI Dashboard for the Synergy Agent."""

    def __init__(self, model_name: str = ""):
        self.model_name = model_name
        self.task = ""
        self.attempt = 1
        self.start_time = 0.0
        self.steps_taken = 0
        self.total_tokens = 0
        self.status_message = "Agent Ready"
        self.current_step_panel = None
        
        # History to display in the body zone
        self._history: list[any] = []
        
        # Layout and Live display core
        self.layout = Layout()
        self.live: Live | None = None

    # ── Layout Construction ───────────────────────────────────────────

    def _setup_layout(self) -> None:
        """Initialize the three-zone dashboard layout."""
        self.layout.split(
            Layout(name="header", size=6),
            Layout(name="body", ratio=1),
            Layout(name="footer", size=3),
        )
        self._update_header()
        self._update_footer()
        self._update_body()

    def _update_header(self) -> None:
        """Render the persistent top header."""
        grid = Table.grid(expand=True)
        grid.add_column(justify="left")
        grid.add_column(justify="right")
        
        title = Text()
        title.append(f"{AGENT_NAME} ", style=f"bold {PRIMARY}")
        title.append(f"{AGENT_VERSION}", style=DIM)
        
        info = Text()
        if self.attempt > 1:
            info.append(f"Attempt {self.attempt} ", style="bold yellow")
            info.append("│ ", style=DIM)
        if self.model_name:
            info.append(f"Model: google/gemma-4-31B-it", style=DIM)
        
        grid.add_row(title, info)
        
        task_text = Text()
        task_text.append("\n📋 Task: ", style="bold white")
        task_text.append(_trunc(self.task, 150), style="white")
        
        self.layout["header"].update(Panel(
            Group(grid, task_text),
            border_style=PRIMARY,
            title=f"[bold {PRIMARY}]Agent Session[/]",
            box=box.ROUNDED,
            padding=(1, 2)
        ))

    def _update_footer(self) -> None:
        """Render the persistent bottom metrics bar."""
        elapsed = time.time() - self.start_time if self.start_time else 0
        
        footer_table = Table(
            show_header=False,
            show_edge=False,
            show_lines=False,
            box=None,
            padding=(0, 2),
            expand=True,
        )
        footer_table.add_column("c1", justify="left", ratio=1)
        footer_table.add_column("c2", justify="center", ratio=1)
        footer_table.add_column("c3", justify="right", ratio=1)

        steps = Text.assemble((f"{self.steps_taken}", f"bold white"), (" steps", DIM))
        tokens = Text.assemble((f"{self.total_tokens:,}", "bold white"), (" tokens", DIM))
        
        mins, secs = divmod(int(elapsed), 60)
        timer = Text.assemble((f"{mins}m {secs}s", "bold white"), (" elapsed", DIM))

        footer_table.add_row(steps, tokens, timer)
        
        self.layout["footer"].update(Panel(
            footer_table,
            border_style=DIM,
            padding=(0, 1),
            box=box.ROUNDED
        ))

    def _update_body(self) -> None:
        """Compose the body from history and active step panel."""
        elements = []
        
        # Show last 15 history lines
        for item in self._history[-15:]:
            elements.append(item)
            elements.append("") # Spacer
            
        if self.current_step_panel:
            elements.append(self.current_step_panel)
        else:
            elements.append(Panel(
                Text(f"⏳ {self.status_message}", justify="center", style=THINKING),
                border_style=DIM,
                padding=(1, 1),
                box=box.ROUNDED
            ))

        self.layout["body"].update(Group(*elements))

    # ── Lifecycle ─────────────────────────────────────────────────────

    def start(self, task: str, attempt: int = 1) -> None:
        """Initialize the task, setup layout, and start Live display."""
        self.task = task
        self.attempt = attempt
        self.start_time = time.time()
        self.steps_taken = 0
        self.total_tokens = 0
        self._history = []
        self.current_step_panel = None
        self.status_message = "Agent Initializing..."
        
        self._setup_layout()
        
        self.live = Live(
            self.layout,
            console=_console,
            screen=True, 
            auto_refresh=True,
            refresh_per_second=4,
            redirect_stdout=True,
        )
        self.live.start()

    def stop(self) -> None:
        """Stop the Live display and leave the dashboard view."""
        if self.live:
            self.live.stop()
            self.live = None
        
        # Clear screen before printing final result to remove terminal artifacts
        _console.clear()
        _console.print(self.layout)

    # ── Step rendering ────────────────────────────────────────────────

    def render_step(
        self,
        step_num: int,
        total_steps: int,
        thought: str,
        tool_name: str,
        tool_input: str,
        result: str,
        duration: float,
        success: bool,
    ) -> None:
        """Update historical steps and create new active step panel."""
        self.steps_taken = step_num
        self.status_message = "Processing Step..."

        # 1. Thought/Logic Panel
        thought_panel = Panel(
            Text(_trunc(thought, 800), style=THINKING),
            title=f"[{THINKING}]💭 Thinking[/]",
            border_style=THINKING,
            padding=(1, 2),
            box=box.ROUNDED
        )

        tool_info = Text.assemble(
            (f" 🔧 {tool_name or 'Logic'} ", f"bold {TOOL}"),
            (f"→ ", DIM),
            (_trunc(tool_input, 150), "white")
        )

        # 2. Result Panel
        result_style = SUCCESS if success else ERROR
        result_title = "✓ Success" if success else "✗ Error"
        result_panel = Panel(
            Text(_trunc(result, 1200), style=result_style),
            title=f"[{result_style}]{result_title}[/]",
            border_style=result_style,
            padding=(1, 2),
            box=box.ROUNDED
        )

        self.current_step_panel = Panel(
            Group(thought_panel, "", tool_info, "", result_panel),
            title=f"[bold white]Step {step_num}[/]",
            border_style=STEP_BORDER,
            subtitle=f"[{DIM}]{duration:.1f}s[/]",
            padding=(1, 1),
            box=box.ROUNDED
        )

        # 3. Add a one-liner of the COMPLETED step to history
        icon = "✓" if success else "✗"
        icon_style = SUCCESS if success else ERROR
        history_line = Text.assemble(
            (f" {icon} ", f"bold {icon_style}"),
            (f"Step {step_num} ", "bold white"),
            (f"│ ", DIM),
            (f"{tool_name or 'Logic'} ", f"bold {TOOL}"),
            (_trunc(tool_input, 80), DIM),
            (f"  {duration:.1f}s", f"italic {DIM}"),
        )
        self._history.append(history_line)
        
        self._update_header()
        self._update_footer()
        self._update_body()

    def set_status(self, message: str) -> None:
        """Live update for thinking/running statuses."""
        self.status_message = message
        self._update_body()
        self._update_footer()

    # ── Results & Input ───────────────────────────────────────────────

    def show_final_result(self, result: str) -> None:
        """Display final answer panel and stop the TUI."""
        self.status_message = "Task Completed"
        self.current_step_panel = Panel(
            Text(result, style="bold white"),
            title=f"[bold {SUCCESS}]✨ Final Answer[/]",
            border_style=SUCCESS,
            padding=(2, 4),
            box=box.HEAVY
        )
        self._update_body()
        self._update_header()
        self._update_footer()
        
        # Longer pause for final visualization
        time.sleep(2.5)
        self.stop()

    def show_error(self, error: str) -> None:
        """Show a fatal error and stop."""
        self.status_message = "An error occurred"
        self.current_step_panel = Panel(
            Text(str(error), style=f"bold {ERROR}"),
            title=f"[bold {ERROR}]❌ Fatal Error[/]",
            border_style=ERROR,
            padding=(2, 4),
            box=box.HEAVY
        )
        self._update_body()
        self._update_footer()
        time.sleep(3)
        self.stop()

    def get_input(self) -> str:
        """Normal terminal input. Use Bold White fix for font visibility."""
        _console.print()
        # default_style="bold white" ensures the typed text is visible on dark backgrounds
        return Prompt.ask(
            f"[{INPUT_ARROW}]›[/]", 
            default="", 
            show_default=False
        )

    def show_banner(self) -> None:
        """Fancy startup banner."""
        _console.clear()
        banner_text = Text(justify="center")
        banner_text.append("\n╔═══════════════════════════════════════╗\n", style=f"bold {PRIMARY}")
        banner_text.append("║                                       ║\n", style=f"bold {PRIMARY}")
        banner_text.append("║", style=f"bold {PRIMARY}")
        banner_text.append(f"   ⚡  SYNERGY AGENT  ⚡   ", style=f"bold bright_white")
        banner_text.append("║\n", style=f"bold {PRIMARY}")
        banner_text.append("║", style=f"bold {PRIMARY}")
        banner_text.append(f"     Premium Dashboard UI    ", style=f"bold {THINKING}")
        banner_text.append("║\n", style=f"bold {PRIMARY}")
        banner_text.append("║                                       ║\n", style=f"bold {PRIMARY}")
        banner_text.append("╚═══════════════════════════════════════╝", style=f"bold {PRIMARY}")
        _console.print(banner_text)
        _console.print(f"\n[dim]Model: google/gemma-4-31B-it | Type [/dim][bold {PRIMARY}]/help[/bold] [dim]for commands[/dim]\n")
