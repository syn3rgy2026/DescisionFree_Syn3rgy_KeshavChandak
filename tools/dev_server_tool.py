"""
dev_server_tool.py
------------------
Start and stop background development servers (Next.js, Vite, Flask, etc.).
Keeps track of running processes so the agent can start a server, test it
in the browser, and stop it when done.
"""

import os
import signal
import subprocess
import time
from smolagents import tool

# Active server processes: name → Popen object
_servers = {}


@tool
def start_dev_server(name: str, command: str, project_dir: str, port: int = 3000, wait_seconds: int = 5) -> str:
    """Start a development server in the background. The server runs as a
    subprocess so the agent can continue working while it's running.
    Use browser_navigate or browser_screenshot to test it afterwards.

    Args:
        name: A short label for the server (e.g. 'nextjs', 'vite', 'flask').
        command: Shell command to start the server (e.g. 'npm run dev', 'python app.py').
        project_dir: Directory to run the command in.
        port: Port the server listens on (used for status messages).
        wait_seconds: Seconds to wait after starting before checking if alive.

    Returns:
        str: Status message with the URL to access the server.
    """
    if name in _servers and _servers[name].poll() is None:
        return f"Server '{name}' is already running on port {port}. Stop it first with stop_dev_server."

    if not os.path.isdir(project_dir):
        return f"ERROR: Directory not found: {project_dir}"

    try:
        proc = subprocess.Popen(
            command,
            shell=True,
            cwd=project_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid,
        )
        _servers[name] = proc

        time.sleep(wait_seconds)

        if proc.poll() is not None:
            stderr = proc.stderr.read().decode("utf-8", errors="replace")[:1000]
            del _servers[name]
            return f"❌ Server '{name}' crashed immediately:\n{stderr}"

        return (
            f"✅ Server '{name}' started (PID {proc.pid})\n"
            f"URL: http://localhost:{port}\n"
            f"Command: {command}\n"
            f"Use browser_navigate('http://localhost:{port}') to test it."
        )
    except Exception as e:
        return f"ERROR starting server: {e}"


@tool
def stop_dev_server(name: str) -> str:
    """Stop a running development server by name.

    Args:
        name: The label used when starting the server.

    Returns:
        str: Confirmation that the server was stopped.
    """
    if name not in _servers:
        return f"No server named '{name}' is tracked. Running servers: {list(_servers.keys()) or 'none'}"

    proc = _servers[name]
    if proc.poll() is not None:
        del _servers[name]
        return f"Server '{name}' already exited (code {proc.returncode})."

    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        proc.wait(timeout=5)
    except Exception:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except Exception:
            pass

    del _servers[name]
    return f"✅ Server '{name}' stopped."


@tool
def list_dev_servers() -> str:
    """List all tracked development servers and their status.

    Returns:
        str: Table of server names, PIDs, and alive/dead status.
    """
    if not _servers:
        return "No dev servers running."

    lines = ["Name | PID | Status"]
    lines.append("---|---|---")
    for name, proc in _servers.items():
        alive = "🟢 RUNNING" if proc.poll() is None else f"🔴 EXITED ({proc.returncode})"
        lines.append(f"{name} | {proc.pid} | {alive}")
    return "\n".join(lines)


@tool
def get_server_logs(name: str, lines: int = 50) -> str:
    """Get recent output from a running dev server. Useful for debugging
    server errors or checking if a request was received.

    Args:
        name: The server label.
        lines: Number of lines to return (default 50).

    Returns:
        str: Recent stdout + stderr from the server process.
    """
    if name not in _servers:
        return f"No server named '{name}'. Running: {list(_servers.keys()) or 'none'}"

    proc = _servers[name]
    output = ""
    try:
        if proc.stdout and proc.stdout.readable():
            raw = proc.stdout.read(4096)
            if raw:
                output += raw.decode("utf-8", errors="replace")
    except Exception:
        pass
    try:
        if proc.stderr and proc.stderr.readable():
            raw = proc.stderr.read(4096)
            if raw:
                output += "\n[stderr]\n" + raw.decode("utf-8", errors="replace")
    except Exception:
        pass

    if not output.strip():
        alive = "running" if proc.poll() is None else "exited"
        return f"No new output from '{name}' (server is {alive})."
    return output[-3000:]


DEV_SERVER_TOOLS = [
    start_dev_server,
    stop_dev_server,
    list_dev_servers,
    get_server_logs,
]
