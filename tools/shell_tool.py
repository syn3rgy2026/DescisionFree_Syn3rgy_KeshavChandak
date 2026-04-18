# OWNER: Person 2
"""
shell_tool.py
-------------
Executes shell commands in a controlled subprocess with a configurable
timeout (config.SHELL_TIMEOUT). Always requests human confirmation before
running any destructive command (rm, sudo, etc.).
"""

import subprocess
import config

# Importing the human confirmation tool you (Person 2) are also building
from tools.human_confirm import ask_human_confirmation

def run_command(command: str, require_confirm: bool = False) -> dict:
    """
    Execute a shell command and return its stdout, stderr, and exit code.

    Args:
        command (str): Shell command string to execute.
        require_confirm (bool): If True, prompt the user for confirmation first.

    Returns:
        dict: Keys 'stdout', 'stderr', 'returncode'.
    """
    if require_confirm:
        # Pause the agent and ask the human for permission
        user_response = ask_human_confirmation(
            action=f"Run shell command: `{command}`",
            reason="This command was flagged as potentially destructive or touches sensitive system directories.",
            risk_level="HIGH"
        )
        
        # If the human says anything other than YES, abort the execution
        if user_response.strip().upper() != "YES":
            return {
                'stdout': '',
                'stderr': 'Execution cancelled by user.',
                'returncode': -1 # Custom code to indicate manual cancellation
            }

    try:
        # Fetch the timeout from config, defaulting to 30 seconds if missing
        timeout_limit = getattr(config, 'SHELL_TIMEOUT', 30)
        
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout_limit
        )
        
        return {
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }
        
    except subprocess.TimeoutExpired:
        return {
            'stdout': '',
            'stderr': f"Command timed out after {timeout_limit} seconds",
            'returncode': 124 # Standard Linux timeout exit code
        }
    except Exception as e:
        return {
            'stdout': '',
            'stderr': f"An unexpected error occurred: {str(e)}",
            'returncode': 1
        }


def is_destructive(command: str) -> bool:
    """
    Heuristically determine whether a command is potentially destructive.

    Args:
        command (str): Command string to inspect.

    Returns:
        bool: True if the command should be flagged for confirmation.
    """
    # The exact risky keywords specified in the project guide
    risky_keywords = [
        "rm", 
        "sudo", 
        "pip install", 
        "/etc/", 
        "/sys/", 
        "/usr/", 
        "format", 
        "shutdown"
    ]
    
    # We pad 'rm' and 'sudo' with spaces in our check to avoid accidentally 
    # flagging safe words that contain those letters (like 'arm' or 'pseudocode')
    # For directory paths or exact commands, we check them directly.
    padded_command = f" {command} "
    
    if " rm " in padded_command or " sudo " in padded_command:
        return True
        
    for keyword in ["pip install", "/etc/", "/sys/", "/usr/", "format", "shutdown"]:
        if keyword in command:
            return True
            
    return False


def safe_run(command: str) -> dict:
    """
    Run a command, automatically requiring confirmation if it looks destructive.

    Args:
        command (str): Shell command string.

    Returns:
        dict: Same structure as run_command return value.
    """
    # Check if the command hits our heuristic danger list
    needs_confirm = is_destructive(command)
    
    # Pass it to the main executor
    return run_command(command, require_confirm=needs_confirm)


# --- TEST BLOCK ---
if __name__ == "__main__":
    import os
    
    print("\n" + "="*40)
    print("TESTING SHELL TOOL")
    print("="*40 + "\n")

    # Test 1: A completely safe command
    print("--- Test 1: Safe Command (pwd) ---")
    result_safe = safe_run("pwd")
    print(f"Stdout:\n{result_safe['stdout'].strip()}")
    print("-" * 40 + "\n")

    # Test 2: Another safe command with arguments
    print("--- Test 2: Safe Command (echo) ---")
    result_echo = safe_run("echo hello world")
    print(f"Stdout:\n{result_echo['stdout'].strip()}")
    print("-" * 40 + "\n")

    # Test 3: A risky command that MUST trigger the confirmation prompt
    print("--- Test 3: Risky Command (rm) ---")
    print("Expected: You should be prompted to confirm this action.")
    # We use a dummy file path so we don't accidentally delete anything real if you type YES
    result_risky = safe_run("rm /tmp/dummy_test_file.txt") 
    print(f"Result Code: {result_risky['returncode']}")
    print(f"Stderr/Stdout: {result_risky['stderr']} {result_risky['stdout']}")
    print("-" * 40 + "\n")
    
    print("Testing complete. If Test 3 paused and asked for confirmation, you are good to go!")