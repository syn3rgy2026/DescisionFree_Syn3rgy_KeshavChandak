"""
app.py
------
Synergy Agent — Professional IDE-style Agent Panel (Dark Mode)

Clean, functional UI with a three-column layout:
  [ PLAN ]  |  [ THINKING (MAIN) ]  |  [ CONTEXT / FINDINGS ]

Aura: Professional, deep charcoal dark mode with blue accents.
Focus: The agent's thought process is central. The execution plan is a flowchart.

Drag-and-drop: drop files from Finder onto the terminal input to attach them.
"""

from __future__ import annotations

import os
import time
import asyncio
import re
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Static, Input, RichLog, ListView, ListItem,
    DataTable, ProgressBar, Label,
)
from textual.reactive import reactive
from textual.widget import Widget
from rich.text import Text
from rich.style import Style

from ui.file_context import extract_paths, build_augmented_task


# ═══════════════════════════════════════════════════════════
# Color Palette — Professional Dark (GitHub / VS Code)
# ═══════════════════════════════════════════════════════════
ACCENT =  "#58a6ff"   # Primary Blue
GREEN =   "#3fb950"   # Success
RED =     "#f85149"   # Error
AMBER =   "#d29922"   # In-progress / Warning
DIM =     "#8b949e"   # Muted text
BODY =    "#c9d1d9"   # Body text
WHITE =   "#ffffff"   # Bright white
BG =      "#0d1117"   # Background (Deep charcoal)
PANEL =   "#161b22"   # Secondary Background


# ═══════════════════════════════════════════════════════════
# Human-readable tool name mapping
# ═══════════════════════════════════════════════════════════

TOOL_LABELS = {
    "python_interpreter":      "Thinking",
    "web_search":              "Searching web",
    "visit_url":               "Reading webpage",
    "send_email":              "Sending email",
    "create_ppt":              "Generating slides",
    "github_push":             "Pushing to GitHub",
    "vercel_deploy":           "Deploying App",
    "final_answer":            "Finishing",
}

def _existing_fs_paths(paths: list[str]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for p in paths:
        try:
            ap = str(Path(p).expanduser().resolve(strict=False))
        except OSError:
            continue
        if os.path.isfile(ap) or os.path.isdir(ap):
            if ap not in seen:
                seen.add(ap)
                ordered.append(ap)
    return ordered


def _paths_from_final_answer(text: str) -> list[str]:
    """Pull absolute file paths from 'Files created/modified' style lists in the final answer."""
    if not text:
        return []
    out: list[str] = []
    seen: set[str] = set()
    for line in str(text).splitlines():
        s = line.strip()
        if not s.startswith("- "):
            continue
        raw = s[2:].strip()
        if not raw or ("/" not in raw and "~" not in raw and not raw.startswith("file:")):
            continue
        raw = raw.split()[0].strip("`")
        if raw.startswith("file:"):
            raw = raw[5:].lstrip("/")
            if not raw.startswith("/"):
                raw = "/" + raw
        p = os.path.abspath(os.path.expanduser(raw))
        if os.path.isfile(p) and p not in seen:
            seen.add(p)
            out.append(p)
    return out


def _human_label(tool_name: str, code: str = "") -> str:
    """Determine a user-friendly action label."""
    if tool_name != "python_interpreter":
        return TOOL_LABELS.get(tool_name, tool_name.replace("_", " ").title())

    # Analyze code to find intent
    code_lower = str(code).lower()
    if "final_answer" in code_lower: return "Finishing task"
    if "web_search" in code_lower:   return "Searching web"
    if "visit_url" in code_lower:    return "Reading page"
    if "write_file" in code_lower:   return "Saving file"
    if "read_file" in code_lower:    return "Opening file"
    if "deploy" in code_lower:       return "Deploying"
    if "git" in code_lower:          return "Git operation"
    
    return "Thinking"


# ═══════════════════════════════════════════════════════════
# Custom Widgets
# ═══════════════════════════════════════════════════════════


class AttachedFilesBar(Static):
    """Shows attached file names when the user drags files onto the input."""

    attached: reactive[list] = reactive(list, always_update=True)

    def render(self) -> Text:
        files = self.attached
        if not files:
            return Text("")
        names = [Path(p).name for p in files]
        t = Text()
        t.append(" 📎 ", style=f"bold {ACCENT}")
        t.append(f"{len(files)} file{'s' if len(files) > 1 else ''} attached: ", style=WHITE)
        t.append(", ".join(names[:5]), style=ACCENT)
        if len(names) > 5:
            t.append(f" +{len(names) - 5} more", style=DIM)
        t.append("   /clear-files to remove", style=DIM)
        return t


class AgentHeader(Static):
    """Refined header with status metrics."""

    steps = reactive(0)
    tokens = reactive(0)
    elapsed = reactive(0.0)

    def render(self) -> Text:
        mins, secs = divmod(int(self.elapsed), 60)
        t = Text()
        t.append(" Synergy Agent ", style=f"bold {ACCENT}")
        t.append(" │ ", style="#30363d")
        t.append(f"{self.steps} steps", style=DIM)
        t.append(" │ ", style="#30363d")
        t.append(f"{self.tokens:,} tokens", style=DIM)
        t.append(" │ ", style="#30363d")
        t.append(f"{mins:02d}:{secs:02d}", style=WHITE)
        return t


class TaskHeader(Static):
    """Mission / Task description."""

    task_text = reactive("")

    def render(self) -> Text:
        t = Text()
        task = self.task_text.replace("\n", " ").strip()
        if not task:
            t.append(" Standing by...", style=DIM)
            return t
        t.append(" Task: ", style=f"bold {ACCENT}")
        t.append(task[:60] + "..." if len(task) > 60 else task, style=WHITE)
        return t


# Tool icons for visual clarity
_TOOL_ICONS = {
    "Thinking": "💭",
    "Searching web": "🔍",
    "Reading page": "📄",
    "Saving file": "💾",
    "Opening file": "📂",
    "Sending email": "✉️",
    "Generating slides": "📊",
    "Deploying": "🚀",
    "Pushing to GitHub": "📤",
    "Git operation": "📤",
    "Finishing task": "✅",
    "Planning": "📋",
    "Strategy": "◇",
    "Creating slides": "📊",
    "Starting...": "⚡",
    "Starting…": "⚡",
    "Done ✓": "🏁",
    "…": "·",
}


_SPIN = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"


class PlanTree(Static):
    """Live execution graph — numbered steps, pulse on active, learning badges."""

    plan_steps: reactive[list] = reactive(list, always_update=True)
    _anim = reactive(0)

    def on_mount(self) -> None:
        self.set_interval(0.11, self._tick_anim)

    def _tick_anim(self) -> None:
        steps = self.plan_steps
        if not steps:
            return
        if any(len(s) > 2 and s[1] == "active" for s in steps):
            self._anim += 1

    def render(self) -> Text:
        t = Text()
        steps = self.plan_steps
        if not steps:
            t.append("\n  Awaiting task — flow builds here as the agent runs.\n", style=DIM)
            return t

        spin = _SPIN[self._anim % len(_SPIN)]
        t.append("\n", style=DIM)

        for i, row in enumerate(steps):
            label, status, detail = row[0], row[1], row[2]
            badge = row[3] if len(row) > 3 else ""
            is_last = i == len(steps) - 1
            display_label = label if label else "Processing"
            icon_key = display_label
            m = re.match(r"^\d+\s*·\s*(.+)$", display_label)
            if m:
                icon_key = m.group(1).strip()
            icon = _TOOL_ICONS.get(icon_key) or _TOOL_ICONS.get(display_label, "●")
            idx = f"{i + 1:02d}"

            if status == "active":
                t.append(f" {spin} ", style=f"bold {ACCENT}")
                t.append(f"{idx} ", style=DIM)
                t.append(f"{icon} ", style=ACCENT)
                t.append(f"{display_label}\n", style=f"bold {WHITE}")
                if detail:
                    t.append(f"     {detail}\n", style=DIM)
            elif status == "done":
                t.append(" ✓ ", style=f"bold {GREEN}")
                t.append(f"{idx} ", style=DIM)
                t.append(f"{icon} ", style=GREEN)
                t.append(f"{display_label}", style=BODY)
                if detail:
                    t.append(f"  {detail}", style=DIM)
                t.append("\n")
            elif status == "error":
                t.append(" ↯ ", style=f"bold {RED}")
                t.append(f"{idx} ", style=DIM)
                t.append(f"{icon} ", style=AMBER)
                t.append(f"{display_label}\n", style=f"bold {AMBER}")
                if detail:
                    t.append(f"     {detail}\n", style=AMBER)
                if badge == "learn":
                    t.append("     ", style=DIM)
                    t.append("saved to memory", style=f"italic {ACCENT}")
                    t.append(" · next run uses this lesson\n", style=DIM)
            else:
                t.append(" ○ ", style=DIM)
                t.append(f"{idx} ", style=DIM)
                t.append(f"{display_label}\n", style=DIM)

            if not is_last:
                if status == "error":
                    t.append("     ", style=DIM)
                    t.append("adapt → retry\n", style=f"italic {ACCENT}")
                else:
                    t.append("     │\n", style="#30363d")

        return t


class StepWidget(Widget):
    """Detailed action item in the scrollable log."""

    status = reactive("pending")
    label = reactive("")
    detail = reactive("")
    error_text = reactive("")
    duration = reactive(0.0)
    _pulse_on = reactive(True)

    def __init__(self, label: str, detail: str = "", **kwargs):
        super().__init__(**kwargs)
        self._pulse_timer = None
        self.label = label
        self.detail = detail
        self.status = "active"

    def on_mount(self) -> None:
        self._pulse_timer = self.set_interval(0.6, self._pulse)

    def _pulse(self) -> None:
        if self.status == "active":
            self._pulse_on = not self._pulse_on
        elif self._pulse_timer:
            self._pulse_timer.stop()

    def render(self) -> Text:
        t = Text()
        
        # Indicator
        if self.status == "active":
            dot = "●" if self._pulse_on else "○"
            t.append(f" {dot} ", style=f"bold {ACCENT}")
        elif self.status == "done":
            t.append(" ✓ ", style=f"bold {GREEN}")
        elif self.status == "error":
            t.append(" ⚠ ", style=f"bold {AMBER}")
        else:
            t.append(" ○ ", style=DIM)

        t.append(f"{self.label} ", style=WHITE if self.status == "active" else DIM)
        
        if self.duration > 0:
            t.append(f"({self.duration:.1f}s)", style=DIM)
            
        if self.status == "active" and self.detail:
            t.append(f"\n   {self.detail[:70]}", style=DIM)
        
        if self.error_text:
            t.append(f"\n   ⚠ {self.error_text[:70]}", style=AMBER)

        return t

    def watch_status(self, new_status: str) -> None:
        self.remove_class("pending", "active", "done", "error")
        self.add_class(new_status)
        if new_status != "active" and getattr(self, "_pulse_timer", None):
            self._pulse_timer.stop()


class FooterHints(Static):
    def render(self) -> Text:
        return Text(" /help  /clear  /exit", style=DIM)


class SessionInsight(Static):
    """One-line live status: errors, recovery, learning (xAI-style strip)."""

    message = reactive("")
    tone = reactive("dim")  # dim | accent | warn | ok

    def render(self) -> Text:
        if not self.message.strip():
            return Text(" Ready — reasoning and tool trace stream to the center panel.", style=DIM)
        styles = {
            "dim": DIM,
            "accent": ACCENT,
            "warn": AMBER,
            "ok": GREEN,
        }
        st = styles.get(self.tone, DIM)
        return Text(self.message, style=st)


# ═══════════════════════════════════════════════════════════
# Main App
# ═══════════════════════════════════════════════════════════


class SynergyAgentApp(App):
    """Professional, Flow-focused Agent Dashboard."""

    CSS_PATH = "app.tcss"
    TITLE = "Synergy Agent"

    start_time: float = 0.0
    _step_widgets: list[StepWidget] = []
    _plan_items: list = []
    _seen_findings: set = set()
    _seen_contexts: set = set()
    _timer_handle = None
    agent_busy: bool = False
    _awaiting_confirmation: bool = False  # True while waiting for human YES/NO
    _attached_files: list[str] = []       # Paths from drag-and-drop

    def compose(self) -> ComposeResult:
        yield AgentHeader(id="agent-header")

        with Horizontal(id="main-body"):
            # LEFT: Planning & Steps (The "How")
            with Vertical(id="left-column"):
                yield TaskHeader(id="task-header")
                yield SessionInsight(id="session-insight")
                yield Static(Text(" Execution flow ", style=f"bold {ACCENT}"), id="plan-section-label")
                yield ScrollableContainer(PlanTree(id="plan-tree"), id="plan-scroll")
                yield Static(Text(" Step log ", style=f"bold {DIM}"), id="log-section-label")
                yield ScrollableContainer(id="steps-feed")
                with Horizontal(id="progress-row"):
                    yield ProgressBar(total=100, show_eta=False, id="progress-bar")

            # CENTER: Thinking (The "Process") — Dominant column
            with Vertical(id="center-column"):
                yield Static(" Agent reasoning ", id="activity-title")
                yield RichLog(id="activity-panel", wrap=True, highlight=True, markup=True)

            # RIGHT: Results (The "What")
            with Vertical(id="right-column"):
                yield Static(" Context ", id="context-title")
                yield ListView(id="context-panel")
                yield Static(" Findings ", id="findings-title")
                yield DataTable(id="findings-panel")

        yield AttachedFilesBar(id="attached-files-bar")
        yield Static("  Enter task · /clear reset · /exit quit · drag files to attach ", id="input-hint")
        yield Input(placeholder="Describe what you want the agent to do… (drag files here)", id="agent-input")

    def on_mount(self) -> None:
        # Register this app as the TUI bridge for human confirmation prompts
        from tools.human_confirm import set_tui_app
        set_tui_app(self)

        self.query_one("#findings-panel", DataTable).add_columns("Item", "Status")
        self.query_one("#activity-panel", RichLog).write(
            Text("Stand by for a task. You will see plans, tool steps, failures, and recoveries here in real time.", style=DIM)
        )
        self.start_time = time.time()
        self._timer_handle = self.set_interval(1.0, self._tick_timer)

    def _tick_timer(self) -> None:
        self.query_one("#agent-header", AgentHeader).elapsed = time.time() - self.start_time

    # ── API for callbacks ──────────────────────────────

    def set_task(self, task: str) -> None:
        self.query_one("#task-header", TaskHeader).task_text = task

    def set_plan(self, steps: list) -> None:
        """Accept (label, status, detail) or (label, status, detail, badge) tuples."""
        norm: list[tuple] = []
        for s in steps:
            if len(s) >= 4:
                norm.append((s[0], s[1], s[2], s[3]))
            else:
                norm.append((s[0], s[1], s[2], ""))
        self._plan_items = norm
        self.query_one("#plan-tree", PlanTree).plan_steps = norm

    def set_insight(self, message: str, tone: str = "dim") -> None:
        """Update the live strip under the task (dim | accent | warn | ok)."""
        strip = self.query_one("#session-insight", SessionInsight)
        strip.message = message
        strip.tone = tone if tone in ("dim", "accent", "warn", "ok") else "dim"

    def add_step(self, label: str, detail: str = "") -> None:
        step = StepWidget(label=label, detail=detail)
        self.query_one("#steps-feed", ScrollableContainer).mount(step)
        step.scroll_visible()
        self._step_widgets.append(step)
        self.query_one("#agent-header", AgentHeader).steps += 1
        self._update_progress()

    def mark_step_done(self, duration: float, success: bool = True, error_msg: str = "") -> None:
        if self._step_widgets:
            step = self._step_widgets[-1]
            step.status = "done" if success else "error"
            step.duration = duration
            step.error_text = error_msg
        self._update_progress()

    def log_thinking(self, text: str) -> None:
        log = self.query_one("#activity-panel", RichLog)
        log.write(Text(text, style=BODY))
        log.write(Text(" · " * 28, style="#21262d"))

    def log_artifact_links(self, paths: list[str]) -> None:
        """Show created/updated files with file:// links (clickable in many terminals)."""
        log = self.query_one("#activity-panel", RichLog)
        ordered = _existing_fs_paths(paths)
        if not ordered:
            return
        log.write(Text(""))
        log.write(
            Text(
                "Outputs — open from your terminal (⌘+click / ctrl+click on the path if supported)",
                style=f"bold {ACCENT}",
            )
        )
        for ap in ordered[:50]:
            try:
                uri = Path(ap).resolve(strict=False).as_uri()
            except ValueError:
                uri = ""
            line = Text()
            line.append("  ▸ ", style=DIM)
            if uri:
                line.append(ap, style=Style(color=ACCENT, underline=True, link=uri))
            else:
                line.append(ap, style=ACCENT)
            log.write(line)

    async def stream_thinking(self, text: str) -> None:
        log = self.query_one("#activity-panel", RichLog)
        log.clear()
        for i in range(0, len(text), 2):
            log.write(Text(text[i:i+2], style=BODY), scroll_end=True)
            await asyncio.sleep(0.01)

    def add_context(self, label: str) -> None:
        # Deduplicate
        short = label[:40] + "..." if len(label) > 40 else label
        if short in self._seen_contexts:
            return
        self._seen_contexts.add(short)
        ctx = self.query_one("#context-panel", ListView)
        ctx.append(ListItem(Label(f"● {short}")))

    def add_finding(self, fact: str, conf: str) -> None:
        # Deduplicate
        if fact in self._seen_findings:
            return
        self._seen_findings.add(fact)
        self.query_one("#findings-panel", DataTable).add_row(fact, conf)

    def update_tokens(self, total_tokens: int) -> None:
        """Update the token count in the header."""
        header = self.query_one("#agent-header", AgentHeader)
        header.tokens = total_tokens

    def _update_progress(self, done: bool = False) -> None:
        import config
        bar = self.query_one("#progress-bar", ProgressBar)
        if done: bar.update(total=100, progress=100)
        else:
            completed = sum(1 for s in self._step_widgets if s.status == "done")
            pct = int((completed / config.MAX_STEPS) * 100) if config.MAX_STEPS else 0
            bar.update(total=100, progress=min(pct, 95))

    # ── Human confirmation bridge ────────────────────────

    def request_human_confirmation(self, message: str) -> None:
        """Called from the worker thread (via call_from_thread) to show a
        confirmation prompt in the TUI input bar."""
        self._awaiting_confirmation = True
        log = self.query_one("#activity-panel", RichLog)
        log.write(Text("\n🛑 HUMAN CONFIRMATION REQUIRED", style=f"bold {RED}"))
        for line in message.splitlines():
            log.write(Text(f"   {line}", style=AMBER))
        log.write(Text("   Type YES to approve, NO to cancel, or alternative instructions.", style=DIM))
        log.write(Text(" · " * 28, style="#21262d"))
        self.set_insight("⏸ Awaiting your confirmation — type YES / NO in the input bar below.", "warn")
        inp = self.query_one("#agent-input", Input)
        inp.placeholder = "🛑 Type YES to approve, NO to cancel, or alternative instructions…"
        inp.focus()

    # ── File attachment helpers ─────────────────────────────────

    def _detect_and_attach(self, text: str) -> None:
        """Scan text for file paths and update the attachment bar."""
        paths = extract_paths(text)
        # Merge with existing (don't replace — user may paste multiple times)
        merged: list[str] = list(self._attached_files)
        for p in paths:
            if p not in merged:
                merged.append(p)
        if merged != self._attached_files:
            self._attached_files = merged
            bar = self.query_one("#attached-files-bar", AttachedFilesBar)
            bar.attached = list(merged)
            if merged:
                self.set_insight(
                    f"📎 {len(merged)} file(s) attached — type your task and press Enter.",
                    "accent",
                )

    def _clear_attachments(self) -> None:
        """Remove all attached files."""
        self._attached_files = []
        try:
            self.query_one("#attached-files-bar", AttachedFilesBar).attached = []
        except Exception:
            pass

    # ── Interaction ─────────────────────────────────────

    def on_paste(self, event) -> None:
        """Catch paste events (including drag-and-drop from Finder).

        When a user drags a file onto a terminal, the terminal pastes the
        absolute path as text.  Textual fires an on_paste event for this.
        We intercept it here to immediately detect file paths.
        """
        if self._awaiting_confirmation:
            return
        pasted = getattr(event, "text", "") or ""
        if pasted:
            self._detect_and_attach(pasted)

    def on_input_changed(self, event: Input.Changed) -> None:
        """Fallback: also check the full input value on changes.

        We debounce filesystem checks to avoid lag on every keystroke:
        only run detection if the input contains a '/' or '~/' prefix.
        """
        if self._awaiting_confirmation:
            return
        val = event.value
        # Quick pre-check: only run expensive path detection if the input
        # looks like it might contain a path
        if "/" in val or val.startswith("~"):
            self._detect_and_attach(val)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        task = event.value.strip()
        if not task: return
        event.input.value = ""

        # If we're waiting for a human confirmation, route the response back
        if self._awaiting_confirmation:
            self._awaiting_confirmation = False
            inp = self.query_one("#agent-input", Input)
            inp.placeholder = "Describe what you want the agent to do… (drag files here)"
            self.log_thinking(f"Confirmation response: {task}")
            self.set_insight("Confirmation received — agent resuming…", "accent")
            from tools.human_confirm import _submit_tui_response
            _submit_tui_response(task)
            return

        if task.lower() == "/exit": self.exit()
        elif task.lower() == "/clear": self.clear_workspace()
        elif task.lower() == "/clear-files":
            self._clear_attachments()
            self.set_insight("Attached files cleared.", "ok")
        elif self.agent_busy:
            self.set_insight("Another run is in progress — wait for it to finish or use /clear.", "warn")
            self.log_thinking("Input ignored while the agent is busy. Use /clear to reset the workspace.")
        else:
            # Build augmented task if files are attached
            attached = list(self._attached_files)
            # Also detect any new paths directly in the submit text (final check)
            inline_paths = extract_paths(task)
            all_paths = list(dict.fromkeys(attached + inline_paths))  # dedupe, order preserved

            if all_paths:
                augmented_task, display_task = build_augmented_task(task, all_paths)
                file_names = ", ".join(Path(p).name for p in all_paths)
                self.log_thinking(
                    f"Attached files\n"
                    f"📎 {len(all_paths)} file(s): {file_names}\n"
                    f"Contents injected into task context for the agent."
                )
            else:
                augmented_task = task
                display_task = task

            self._clear_attachments()
            self.agent_busy = True
            self.clear_workspace()
            self.set_task(display_task)
            self.set_insight("Running — building execution flow from live tool steps…", "accent")
            self.set_plan([("Starting…", "active", "Model load & parse")])
            self.run_worker(lambda: self._run_agent(augmented_task), thread=True)

    def clear_workspace(self) -> None:
        self.query_one("#steps-feed", ScrollableContainer).remove_children()
        self.query_one("#activity-panel", RichLog).clear()
        self.query_one("#context-panel", ListView).clear()
        self.query_one("#findings-panel", DataTable).clear()
        self.query_one("#plan-tree", PlanTree).plan_steps = []
        self._step_widgets = []
        self._plan_items = []
        self._seen_findings = set()
        self._seen_contexts = set()
        self.query_one("#agent-header", AgentHeader).steps = 0
        self.query_one("#session-insight", SessionInsight).message = ""
        self.query_one("#session-insight", SessionInsight).tone = "dim"
        self._clear_attachments()
        self.start_time = time.time()

    def _run_agent(self, task: str) -> None:
        import config as _cfg
        from agent.core_agent import build_agent
        from agent.resilient_llm import is_transient_llm_error
        from ui.callbacks import TextualStepCallback

        max_runs = max(1, int(getattr(_cfg, "AGENT_RUN_MAX_RETRIES", 3)))

        for run_idx in range(max_runs):
            cb = None
            try:
                cb = TextualStepCallback(self, task)
                agent = build_agent(task, step_callbacks=[cb])
                res = agent.run(task)
                self.call_from_thread(
                    self.show_finished,
                    str(res),
                    task,
                    list(cb.collected_errors),
                    list(cb.artifact_paths),
                )
                return
            except Exception as e:
                errs = list(cb.collected_errors) if cb else []
                if run_idx < max_runs - 1 and is_transient_llm_error(e):
                    base = float(getattr(_cfg, "MODEL_RETRY_WAIT_SEC", 2.0))
                    delay = min(45.0, base * (2**run_idx) * 2)
                    self.call_from_thread(
                        self.log_thinking,
                        f"Transient API/network issue (will retry): {str(e)[:400]}\n"
                        f"→ Full run retry {run_idx + 2}/{max_runs} in {delay:.0f}s…",
                    )
                    time.sleep(delay)
                    continue
                self.call_from_thread(self.show_error, str(e), task, errs)
                return

    def show_finished(
        self,
        res: str,
        task: str = "",
        step_errors: list | None = None,
        artifact_paths: list | None = None,
    ) -> None:
        from memory.memory_manager import get_memory_manager

        errs = step_errors or []
        err_blob = "\n---\n".join(errs)[:2000] if errs else ""
        try:
            get_memory_manager().log_task(task or "(no task text)", str(res), "completed", err_blob)
        except Exception:
            pass

        log = self.query_one("#activity-panel", RichLog)
        log.clear()
        log.write(Text(" Done ", style=f"reverse bold {GREEN}"))
        log.write("")
        log.write(Text(res, style=WHITE))
        merged_paths = list(artifact_paths or [])
        merged_paths.extend(_paths_from_final_answer(res))
        merged_paths = list(dict.fromkeys(merged_paths))
        existing_out = _existing_fs_paths(merged_paths)
        self.log_artifact_links(merged_paths)
        had_errors = bool(errs)
        n_art = len(existing_out)
        if had_errors:
            ins = "Finished with earlier step issues — lessons were saved where applicable."
            tone = "warn"
        elif n_art:
            ins = f"Finished — {n_art} path(s) above are clickable where your terminal supports file links."
            tone = "ok"
        else:
            ins = "Finished — no local file paths detected; see final answer for details."
            tone = "ok"
        self.set_insight(ins, tone)
        self.agent_busy = False
        self._update_progress(done=True)
        # Preserve error status, only mark pending/active as done
        if self._plan_items:
            final_plan = []
            for row in self._plan_items:
                l, s, d = row[0], row[1], row[2]
                b = row[3] if len(row) > 3 else ""
                if s in ("error",):
                    final_plan.append((l, s, d, b))
                else:
                    final_plan.append((l, "done", d, b))
            final_plan.append(("Done ✓", "done", "", ""))
            self.set_plan(final_plan)

    def show_error(self, err: str, task: str = "", step_errors: list | None = None) -> None:
        from memory.memory_manager import get_memory_manager

        errs = step_errors or []
        err_blob = "\n---\n".join(errs)[:2000] if errs else str(err)[:2000]
        try:
            get_memory_manager().log_task(
                task or "(no task text)",
                str(err)[:5000],
                "error",
                err_blob,
            )
        except Exception:
            pass

        log = self.query_one("#activity-panel", RichLog)
        log.write(Text(f"\n ERROR: {err}", style=f"bold {RED}"))
        self.set_insight("Run stopped — check the error above and try again or rephrase the task.", "warn")
        self.agent_busy = False

    def action_quit(self) -> None:
        """Clean up the TUI bridge before quitting."""
        from tools.human_confirm import clear_tui_app
        clear_tui_app()
        super().action_quit()
