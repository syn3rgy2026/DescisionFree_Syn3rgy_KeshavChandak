# OWNER: Person 1
"""
skill_router.py
---------------
Maps LLM-requested tool names to concrete tool implementations and
loads the matching skill prompt from the skills/ folder.

Responsibilities:
- Maintain a registry of available tool names → tool callables
- Load and return the .md skill prompt for a given skill name
- Validate that a requested tool exists before dispatching
"""

import config


class SkillRouter:
    """Routes a tool-call name to the correct tool function and skill prompt."""

    def __init__(self):
        """Build the tool registry by importing all tool modules."""
        raise NotImplementedError("Person 1 will implement this")

    def get_tool(self, tool_name: str):
        """
        Return the callable for the requested tool.

        Args:
            tool_name (str): Identifier of the tool (e.g. 'browser', 'shell').

        Returns:
            callable: The tool function to invoke.

        Raises:
            ValueError: If tool_name is not registered.
        """
        raise NotImplementedError("Person 1 will implement this")

    def load_skill_prompt(self, skill_name: str) -> str:
        """
        Read and return the content of a skill .md file.

        Args:
            skill_name (str): Name of the skill file without extension.

        Returns:
            str: Raw markdown content of the skill prompt.
        """
        raise NotImplementedError("Person 1 will implement this")

    def list_tools(self) -> list:
        """
        Return a list of all registered tool names.

        Returns:
            list[str]: Registered tool identifiers.
        """
        raise NotImplementedError("Person 1 will implement this")
