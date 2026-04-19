"""
step_callback.py
----------------
Callback bridge between smolagents and the TUI Dashboard.

Translates internal agent states (Action, Planning, Thinking) into
interactive updates for the AgentCLI dashboard.
"""

import time
from smolagents import ActionStep, PlanningStep
from ui.cli import AgentCLI


class StepCallback:
    """
    Drop-in callback for smolagents CodeAgent.
    Feeds real-time data to the AgentCLI TUI.
    """

    def __init__(self, cli: AgentCLI, max_steps: int = 15):
        self.cli = cli
        self.max_steps = max_steps
        self._step_start = time.time()
        self._total_input_tokens = 0
        self._total_output_tokens = 0

    def __call__(self, step_log) -> None:
        """Called by smolagents after every step."""
        duration = time.time() - self._step_start
        self._step_start = time.time()

        # Update tokens
        token_usage = getattr(step_log, "token_usage", None)
        if token_usage:
            self._total_input_tokens += getattr(token_usage, "input_tokens", 0) or 0
            self._total_output_tokens += getattr(token_usage, "output_tokens", 0) or 0
            self.cli.total_tokens = self._total_input_tokens + self._total_output_tokens

        # Route to appropriate handler
        if isinstance(step_log, PlanningStep):
            self._handle_planning(step_log)
        elif isinstance(step_log, ActionStep):
            self._handle_action(step_log, duration)

    def _handle_planning(self, step: PlanningStep) -> None:
        """Agent is formulating a plan."""
        plan = getattr(step, "plan", "") or "Updating plan..."
        self.cli.set_status(f"📝 Planning: {plan[:50]}...")

    def _handle_action(self, step: ActionStep, duration: float) -> None:
        """Agent completed an action."""
        step_num = getattr(step, "step_number", self.cli.steps_taken + 1)
        
        # Extract thought
        thought = str(getattr(step, "model_output", "")) or "Logical reasoning..."

        # Extract tool info
        tool_name = ""
        tool_input = ""
        tool_calls = getattr(step, "tool_calls", None)
        if tool_calls:
            tc = tool_calls[0]
            tool_name = getattr(tc, "name", "")
            args = getattr(tc, "arguments", {})
            tool_input = str(args)

        # Observation/Result
        result = str(getattr(step, "observations", "")) or str(getattr(step, "action_output", ""))
        error = getattr(step, "error", None)

        # Update CLI
        self.cli.render_step(
            step_num=step_num,
            total_steps=self.max_steps,
            thought=thought,
            tool_name=tool_name,
            tool_input=tool_input,
            result=result or error or "Step complete.",
            duration=duration,
            success=error is None,
        )
