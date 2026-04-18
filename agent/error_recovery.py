# OWNER: Person 1
"""
error_recovery.py
-----------------
Handles graceful error recovery during the agentic loop.

Responsibilities:
- Classify errors (tool failure, LLM refusal, timeout, parse error)
- Decide whether to retry, skip, or abort the current step
- Compose a corrective message to inject back into the conversation
- Log errors to the task log via MemoryManager
"""


class ErrorRecovery:
    """Classifies and recovers from errors that occur during agent execution."""

    def __init__(self, memory_manager=None):
        """
        Initialise with an optional MemoryManager for error logging.

        Args:
            memory_manager: Instance of MemoryManager (may be None in early dev).
        """
        raise NotImplementedError("Person 1 will implement this")

    def handle(self, error: Exception, step: int, context: dict) -> dict:
        """
        Determine recovery strategy for a given error.

        Args:
            error (Exception): The exception that was raised.
            step (int): Current step number in the agentic loop.
            context (dict): Snapshot of the current loop state.

        Returns:
            dict: Recovery action with keys 'strategy' and 'message'.
                  strategy ∈ {'retry', 'skip', 'abort'}
        """
        raise NotImplementedError("Person 1 will implement this")

    def classify_error(self, error: Exception) -> str:
        """
        Map an exception to a human-readable error category string.

        Args:
            error (Exception): The exception to classify.

        Returns:
            str: Error category label.
        """
        raise NotImplementedError("Person 1 will implement this")

    def corrective_message(self, error_category: str, original_action: dict) -> str:
        """
        Build a corrective prompt message to steer the LLM away from the error.

        Args:
            error_category (str): Result of classify_error.
            original_action (dict): The action dict that caused the error.

        Returns:
            str: Message to append to the conversation context.
        """
        raise NotImplementedError("Person 1 will implement this")
