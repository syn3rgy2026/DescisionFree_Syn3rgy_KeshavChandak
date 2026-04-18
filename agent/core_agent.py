# OWNER: Person 1
"""
core_agent.py
-------------
Central orchestrator for Synergy Agent. Responsible for:
- Receiving a user task string
- Loading the master prompt and relevant skill prompts
- Sending requests to the InferX LLM endpoint via the OpenAI-compatible API
- Iterating through a ReAct-style think → act → observe loop (up to MAX_STEPS)
- Delegating tool calls to the appropriate tool modules
- Returning the final answer or artifact path to main.py
"""

import config


class CoreAgent:
    """Manages the full agentic loop for a single user task."""

    def __init__(self):
        """Initialise the agent: load config, prepare skill router and memory manager."""
        raise NotImplementedError("Person 1 will implement this")

    def load_system_prompt(self) -> str:
        """
        Read master_prompt.md and inject current date, available skills,
        and user memory context into the prompt string.

        Returns:
            str: Fully-rendered system prompt.
        """
        raise NotImplementedError("Person 1 will implement this")

    def run(self, task: str) -> str:
        """
        Execute the agentic loop for the given task.

        Args:
            task (str): Raw user instruction from the CLI.

        Returns:
            str: Final response or path to generated output.
        """
        raise NotImplementedError("Person 1 will implement this")

    def _call_llm(self, messages: list) -> dict:
        """
        Send a chat-completion request to the InferX endpoint.

        Args:
            messages (list): OpenAI-style message list.

        Returns:
            dict: Raw API response dict.
        """
        raise NotImplementedError("Person 1 will implement this")

    def _parse_action(self, llm_response: dict) -> tuple:
        """
        Extract the tool name and arguments from an LLM response.

        Args:
            llm_response (dict): Raw response from _call_llm.

        Returns:
            tuple: (tool_name: str, tool_args: dict)
        """
        raise NotImplementedError("Person 1 will implement this")

    def _execute_action(self, tool_name: str, tool_args: dict) -> str:
        """
        Dispatch a parsed action to the correct tool via SkillRouter.

        Args:
            tool_name (str): Name of the tool to invoke.
            tool_args (dict): Arguments for the tool.

        Returns:
            str: Observation string to feed back into the loop.
        """
        raise NotImplementedError("Person 1 will implement this")
