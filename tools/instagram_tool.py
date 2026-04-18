"""
instagram_tool.py
-----------------
Real Instagram posting via browser automation.
Launches Playwright in a SEPARATE SUBPROCESS to avoid threading
conflicts with smolagents' sandboxed code execution.
"""

import os
import sys
import json
import subprocess
from smolagents import tool

# Path to the standalone browser script
_BROWSER_SCRIPT = os.path.join(os.path.dirname(__file__), "_instagram_browser.py")
_PYTHON = sys.executable  # use the same python interpreter


@tool
def login_to_instagram() -> str:
    """
    Opens Instagram in a real visible browser for you to log in.
    A Chrome window will appear — enter your credentials there.
    The tool will automatically detect when you have logged in
    and save your session for future posting.

    Returns:
        A confirmation string once login is detected.
    """
    try:
        result = subprocess.run(
            [_PYTHON, _BROWSER_SCRIPT, "login"],
            capture_output=True,
            text=True,
            timeout=360,  # 6 min max
        )

        # Parse the last line of stdout as JSON
        output_lines = [l.strip() for l in result.stdout.strip().split("\n") if l.strip()]
        if not output_lines:
            return f"❌ No output from browser script. stderr: {result.stderr[:200]}"

        last_line = output_lines[-1]
        try:
            data = json.loads(last_line)
            if data.get("status") == "success":
                return f"✅ {data['message']}"
            else:
                return f"❌ {data.get('message', 'Login failed')}"
        except json.JSONDecodeError:
            return f"❌ Unexpected output: {last_line}"

    except subprocess.TimeoutExpired:
        return "❌ Login timed out. Please try again."
    except Exception as e:
        return f"❌ Login error: {str(e)}"


@tool
def post_to_instagram(image_path: str, caption: str) -> str:
    """
    Posts an image to Instagram using real browser automation.
    Requires login_to_instagram() to have been called first.
    A visible Chrome window will open and perform the posting steps.

    Args:
        image_path: Absolute path to the image file on disk.
        caption: The full caption text including hashtags.

    Returns:
        A JSON string with the posting result status.
    """
    if not os.path.exists(image_path):
        return json.dumps({
            "status": "failed",
            "platform": "instagram",
            "message": f"Image not found at: {image_path}"
        })

    try:
        result = subprocess.run(
            [_PYTHON, _BROWSER_SCRIPT, "post", image_path, caption],
            capture_output=True,
            text=True,
            timeout=120,
        )

        output_lines = [l.strip() for l in result.stdout.strip().split("\n") if l.strip()]
        if not output_lines:
            return json.dumps({
                "status": "failed",
                "platform": "instagram",
                "message": f"No output from browser. stderr: {result.stderr[:200]}"
            })

        last_line = output_lines[-1]
        try:
            data = json.loads(last_line)
            return json.dumps(data, indent=4)
        except json.JSONDecodeError:
            return json.dumps({
                "status": "failed",
                "platform": "instagram",
                "message": f"Unexpected output: {last_line}"
            })

    except subprocess.TimeoutExpired:
        return json.dumps({
            "status": "failed",
            "platform": "instagram",
            "message": "Posting timed out."
        })
    except Exception as e:
        return json.dumps({
            "status": "failed",
            "platform": "instagram",
            "message": str(e)
        })
