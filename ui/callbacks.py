"""
callbacks.py
------------
Textual step callback — builds a DYNAMIC execution graph
from the agent's real actions, not hardcoded steps.

Shows xAI-style thinking: what the agent tried, what failed,
what it's retrying, and its reasoning at each step.
"""

from __future__ import annotations

import os
import time
import re
from typing import TYPE_CHECKING

from smolagents import ActionStep, PlanningStep

if TYPE_CHECKING:
    from ui.app import SynergyAgentApp


def _is_formatting_or_parser_error(err: str) -> bool:
    """True when the failure is from code-action / output structure parsing (smolagents, etc.)."""
    if not err:
        return False
    e = str(err).lower()
    needles = (
        "code parsing",
        "regex pattern",
        "invalid code",
        "could not parse",
        "parse error",
        "parsing failed",
        "malformed",
        "snippet is invalid",
        "expected thought",
        "expected action",
        "unclosed",
        "delimiter",
    )
    return any(n in e for n in needles)


# ── Human-readable tool name mapping ─────────────────────────────────
_TOOL_LABELS = {
    "python_interpreter": "Thinking",
    "web_search":         "Searching web",
    "search_web":         "Searching web",
    "visit_url":          "Reading page",
    "visit_webpage":      "Reading page",
    "send_email":         "Sending email",
    "create_ppt":         "Generating slides",
    "create_ppt_presentation": "Generating slides",
    "github_push":        "Pushing to GitHub",
    "github_create_and_push": "Pushing to GitHub",
    "vercel_deploy":      "Deploying app",
    "final_answer":       "Finishing",
}


def _make_label(tool_name: str, code: str = "") -> str:
    """Determine a user-friendly action label."""
    if tool_name != "python_interpreter":
        return _TOOL_LABELS.get(tool_name, tool_name.replace("_", " ").title())

    code_lower = str(code).lower()
    if "final_answer" in code_lower: return "Finishing task"
    if "web_search" in code_lower:   return "Searching web"
    if "visit_url" in code_lower or "visit_webpage" in code_lower: return "Reading page"
    if "write_file" in code_lower:   return "Saving file"
    if "read_file" in code_lower:    return "Opening file"
    if "deploy" in code_lower:       return "Deploying"
    if "git" in code_lower:          return "Git operation"
    if "create_ppt" in code_lower:   return "Creating slides"
    if "send_email" in code_lower:   return "Sending email"

    return "Thinking"


def _clean_error(raw_error: str) -> str:
    """Strip raw parser dumps, show only the human-readable core."""
    if not raw_error: return ""
    err = str(raw_error).strip()
    if "regex pattern" in err and "not found" in err:
        return "Retrying format..."
    if "code parsing" in err.lower():
        return "Adjusting approach..."
    m = re.search(r'(SyntaxError|NameError|TypeError|ValueError)[:\s]*(.+?)(?:\n|$)', err)
    if m:
        return f"{m.group(1)}: {m.group(2).strip()[:60]}"
    err = re.sub(r'Error in code parsing:.*', '', err, flags=re.DOTALL | re.IGNORECASE)
    err = re.sub(r'Your code snippet is invalid.*', '', err, flags=re.DOTALL | re.IGNORECASE)
    return err[:80].strip() or "Retrying..."


def harvest_artifact_paths(obs: str, code: str, success: bool) -> list[str]:
    """Collect filesystem paths for files touched on a successful step (tool return / code)."""
    if not success:
        return []
    found: list[str] = []
    seen: set[str] = set()

    def add(raw: str) -> None:
        p = os.path.abspath(os.path.expandvars(os.path.expanduser(raw.strip())))
        if os.path.isfile(p) and p not in seen:
            seen.add(p)
            found.append(p)

    blocks = (obs or "", code or "")
    for block in blocks:
        for line in block.splitlines():
            t = line.strip().strip("'\"")
            if len(t) < 2:
                continue
            if t.startswith("~") or (t.startswith("/") and not t.startswith("//")):
                if os.path.isfile(os.path.expanduser(t)):
                    add(t)
    joined = "\n".join(blocks)
    for m in re.finditer(
        r"(?:Written to|wrote to|saved to|Saved to|file at)\s*[:\s]+\s*([/~][^\s\n,;|]+)",
        joined,
        re.I,
    ):
        add(m.group(1))
    for m in re.finditer(
        r"(['\"])(/[A-Za-z0-9_./+\-~]+\.(?:py|md|txt|csv|json|html?|css|pptx|docx|xlsx|png|jpe?g|svg|tsx?|jsx?|ts))\1",
        joined,
        re.I,
    ):
        add(m.group(2))
    return found


def _plan_headline(plan_text: str, max_len: int = 72) -> str:
    """First substantive line of a plan for the flow panel."""
    if not plan_text:
        return "Mapped approach"
    for line in str(plan_text).strip().splitlines():
        line = line.strip()
        if len(line) < 4:
            continue
        if line.lower().startswith(("plan:", "total steps")):
            continue
        return line[:max_len] + ("…" if len(line) > max_len else "")
    return str(plan_text).strip()[:max_len]


def _format_plan_for_log(plan_text: str, limit: int = 520) -> str:
    """Readable planning block for the reasoning panel."""
    body = (plan_text or "").strip()
    if not body:
        return ""
    if len(body) > limit:
        body = body[: limit - 1] + "…"
    return body


def _extract_thinking(model_output: str) -> str:
    """Extract the agent's reasoning from model output."""
    if not model_output:
        return ""
    text = str(model_output).strip()

    # Look for "Thought:" blocks
    m = re.search(r'(?:Thought|Reasoning)[:\s]*(.+?)(?:\n|<code>|```)', text, re.DOTALL | re.IGNORECASE)
    if m:
        t = m.group(1).strip()
        # Clean out any code/HTML artifacts
        t = re.sub(r'</?code>', '', t)
        return t[:300]

    # Fallback to first meaningful line
    for line in text.split("\n"):
        line = line.strip()
        if len(line) > 15 and not line.startswith(("<code>", "```", "import ", "def ", "class ")):
            return line[:300]
    return ""


class TextualStepCallback:
    """
    Builds a DYNAMIC execution graph from real agent steps.
    Each action becomes a node in the Plan flowchart.
    """

    def __init__(self, app: SynergyAgentApp, task: str = ""):
        self.app = app
        self.task = (task or "").strip()
        self._step_start = time.time()
        self._total_tokens = 0
        self._plan_nodes: list[tuple] = []  # (label, status, detail, badge?)
        self.collected_errors: list[str] = []
        self.artifact_paths: list[str] = []
        self._step_index = 0

    def __call__(self, step_log) -> None:
        duration = time.time() - self._step_start
        self._step_start = time.time()

        # Track tokens
        usage = getattr(step_log, "token_usage", None)
        if usage:
            it = getattr(usage, "input_tokens", 0) or 0
            ot = getattr(usage, "output_tokens", 0) or 0
            self._total_tokens += (it + ot)
            self.app.call_from_thread(self.app.update_tokens, self._total_tokens)

        if isinstance(step_log, PlanningStep):
            self._handle_planning(step_log)
        elif isinstance(step_log, ActionStep):
            self._handle_action(step_log, duration)

    def _handle_planning(self, step: PlanningStep) -> None:
        """Show agent planning in the thinking panel."""
        plan_text = getattr(step, "plan", "") or ""
        if plan_text:
            block = _format_plan_for_log(plan_text)
            self.app.call_from_thread(
                self.app.log_thinking,
                f"Planning\n{block}",
            )
            self.app.call_from_thread(
                self.app.set_insight,
                "Planning phase — decomposing the task before tools run.",
                "accent",
            )
            headline = _plan_headline(plan_text)
            self._add_plan_node("Strategy", "done", headline, "")

    def _handle_action(self, step: ActionStep, duration: float) -> None:
        """Process each step — build dynamic plan + thinking stream."""
        step_num = getattr(step, "step_number", 0) or 0
        self._step_index += 1
        si = self._step_index

        # 1. What tool is being used?
        tool_name = ""
        tool_calls = getattr(step, "tool_calls", None)
        if tool_calls:
            tool_name = getattr(tool_calls[0], "name", "")

        code = str(getattr(step, "code_action", "") or "")
        obs = str(getattr(step, "observations", "") or "")
        base_label = _make_label(tool_name, code)
        label = base_label

        # 2. Extract the agent's reasoning
        thinking = _extract_thinking(str(getattr(step, "model_output", "")))

        # 3. Did it succeed or fail?
        error = getattr(step, "error", None)
        success = error is None
        raw_err = str(error).strip() if error else ""
        if raw_err:
            self.collected_errors.append(raw_err[:1500])
            if _is_formatting_or_parser_error(raw_err):
                try:
                    from memory.memory_manager import get_memory_manager

                    get_memory_manager().record_formatting_lesson(raw_err, self.task)
                except Exception:
                    pass
        error_msg = _clean_error(raw_err) if error else ""
        learn = bool(raw_err) and _is_formatting_or_parser_error(raw_err)
        badge = "learn" if learn else ""

        # 4. Stream thinking to center panel (the main show)
        if thinking:
            self.app.call_from_thread(
                self.app.log_thinking,
                f"Reasoning (step {si})\n{thinking}",
            )

        # 5. Build dynamic plan node
        if success:
            self._add_plan_node(label, "done", f"{duration:.1f}s", "")
            self.app.call_from_thread(
                self.app.set_insight,
                f"Step {si} ok — {base_label} ({duration:.1f}s).",
                "ok",
            )
        else:
            self._add_plan_node(label, "error", error_msg, badge)
            if learn:
                self.app.call_from_thread(
                    self.app.set_insight,
                    "Output shape failed parser check — lesson saved; watch the next step adapt.",
                    "warn",
                )
                self.app.call_from_thread(
                    self.app.log_thinking,
                    "Recovery\n"
                    "Parser rejected the last code block or delimiter pattern. "
                    "This run records a format lesson so future tasks start with that constraint in memory.\n"
                    "→ The agent should retry with explicit Thought / Action / code structure.",
                )
            else:
                self.app.call_from_thread(
                    self.app.set_insight,
                    f"Step {si} failed — {error_msg or 'see log'} — continuing if the agent retries.",
                    "warn",
                )
                self.app.call_from_thread(
                    self.app.log_thinking,
                    f"Recovery\nStep {si} hit an error: {error_msg or raw_err[:120]}\n"
                    "→ The agent will try a different tool path or fix on the next step.",
                )

        # 6. Show "what's next" as active node (stored so the next step marks it done)
        if success and base_label != "Finishing task":
            self._plan_nodes.append(("…", "active", "Next tool call", ""))
            self.app.call_from_thread(self.app.set_plan, list(self._plan_nodes))
        else:
            self.app.call_from_thread(self.app.set_plan, list(self._plan_nodes))

        # 7. Add step to the LOG (left panel)
        self.app.call_from_thread(
            self.app.add_step,
            f"{si} · {label}",
            thinking[:72] if thinking else "",
        )
        self.app.call_from_thread(self.app.mark_step_done, duration, success, error_msg)

        for p in harvest_artifact_paths(obs, code, success):
            if p not in self.artifact_paths:
                self.artifact_paths.append(p)

        # 8. Context — show what the agent is working with
        # URLs visited
        urls = re.findall(r'https?://[^\s\'"<>)]+', code + " " + obs)
        for url in urls[:2]:
            self.app.call_from_thread(self.app.add_context, url)

        # Files mentioned
        files = re.findall(r'[a-zA-Z0-9_/.-]+\.(?:py|js|html|css|json|md|pptx|csv|txt)', code + " " + obs)
        for f in files[:2]:
            self.app.call_from_thread(self.app.add_context, f"📄 {f}")
            self.app.call_from_thread(
                self.app.add_finding, f,
                "✓ Created" if success else "✗ Failed"
            )

        # Tool usage as context
        if tool_name and tool_name not in ("python_interpreter", "final_answer"):
            self.app.call_from_thread(self.app.add_context, f"🔧 Using: {tool_name}")

    def _add_plan_node(self, label: str, status: str, detail: str, badge: str = "") -> None:
        """Add a node to the dynamic plan flowchart (4-tuple: label, status, detail, badge)."""
        normalized: list[tuple] = []
        for row in self._plan_nodes:
            l, s, d = row[0], row[1], row[2]
            b = row[3] if len(row) > 3 else ""
            ns = "done" if s == "active" else s
            normalized.append((l, ns, d, b))
        self._plan_nodes = normalized
        self._plan_nodes.append((label, status, detail, badge))
        self.app.call_from_thread(self.app.set_plan, list(self._plan_nodes))
