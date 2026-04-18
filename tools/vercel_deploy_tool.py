"""
vercel_deploy_tool.py
---------------
Deploy projects to Vercel. Handles the full flow automatically:
  1. Ensures Vercel CLI is available (via npx — no global install needed)
  2. Checks if logged in (interactive OAuth in terminal if not)
  3. Deploys the project with visible progress
  4. Opens the live URL in browser

Uses `npx vercel` so no global install is required.
Authentication uses os.system() so it runs INTERACTIVELY in the
user's real terminal — browser opens, user authorizes, token saved.
"""

import os
import subprocess
import webbrowser
from smolagents import tool
from rich.console import Console
from rich.panel import Panel

_console = Console()

# Use npx vercel so it works without global install
VERCEL = "npx -y vercel"


def _cmd(cmd: str, cwd: str = ".", timeout: int = 180) -> dict:
    """Run a shell command and capture output."""
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                           timeout=timeout, cwd=cwd)
        return {"ok": r.returncode == 0, "out": r.stdout.strip(), "err": r.stderr.strip()}
    except subprocess.TimeoutExpired:
        return {"ok": False, "out": "", "err": f"TIMEOUT ({timeout}s)"}
    except Exception as e:
        return {"ok": False, "out": "", "err": str(e)}


def _get_vercel_user() -> str:
    """Get the current Vercel username/email."""
    r = _cmd(f"{VERCEL} whoami", timeout=30)
    return r["out"].strip() if r["ok"] else "unknown"


def _force_clear_credentials() -> None:
    """Force-clear any stale Vercel credentials."""
    _console.print("[dim]🧹 Clearing any stale Vercel credentials...[/dim]")
    # Logout via CLI
    os.system(f"{VERCEL} logout 2>/dev/null || true")
    # Also remove config/auth files directly
    home = os.path.expanduser("~")
    auth_paths = [
        os.path.join(home, ".local", "share", "com.vercel.cli", "auth.json"),
        os.path.join(home, ".vercel", "auth.json"),
        os.path.join(home, "Library", "Application Support", "com.vercel.cli", "auth.json"),
    ]
    for auth_file in auth_paths:
        if os.path.exists(auth_file):
            try:
                os.remove(auth_file)
                _console.print(f"[dim]  Removed {auth_file}[/dim]")
            except Exception:
                pass
    _console.print("[green]✓[/green] Credentials cleared")


def _ensure_logged_in() -> str | None:
    """
    Ensure logged into Vercel. If not, clear stale creds and open
    interactive OAuth flow in the user's REAL terminal via os.system().
    """
    _console.print("[dim]🔑 Checking Vercel authentication...[/dim]")

    r = _cmd(f"{VERCEL} whoami", timeout=30)
    if r["ok"]:
        user = r["out"].strip()
        _console.print(f"[green]✓[/green] Authenticated as [bold cyan]{user}[/bold cyan]")
        return None

    # Not logged in → show clear instructions
    _console.print(Panel(
        "[bold yellow]You are not logged into Vercel.[/bold yellow]\n\n"
        "[white]An interactive login flow will start NOW in your terminal.[/white]\n\n"
        "[bold cyan]What will happen:[/bold cyan]\n"
        "[dim]  1. Vercel CLI will ask you to choose a login method\n"
        "  2. Your browser will open for OAuth authorization\n"
        "  3. Authorize the app in your browser\n"
        "  4. You'll be redirected back and logged in automatically[/dim]\n\n"
        "[bold green]>>> Follow the prompts below <<<[/bold green]",
        title="[bold blue]🌐 Vercel OAuth Login Required[/bold blue]",
        border_style="yellow",
        padding=(1, 2),
    ))

    _console.print("[bold cyan]⏳ Starting Vercel login now...[/bold cyan]\n")

    # os.system() directly inherits the real terminal's stdin/stdout/stderr
    # This works correctly even inside smolagents' CodeAgent sandbox
    exit_code = os.system(f"{VERCEL} login")

    if exit_code != 0:
        _console.print("\n[bold red]❌ Vercel login failed or was cancelled.[/bold red]")
        _console.print("[dim]Try running 'npx vercel login' manually in a separate terminal.[/dim]")
        return "Vercel login failed. Try running 'npx vercel login' manually."

    # Verify login succeeded
    r = _cmd(f"{VERCEL} whoami", timeout=30)
    if r["ok"]:
        user = r["out"].strip()
        _console.print(f"\n[bold green]✅ Successfully authenticated as {user}[/bold green]")
        return None

    return "Still not authenticated after login attempt. Try 'npx vercel login' manually."


# ═══════════════════════════════════════════════════════════════════════
#  Public tools
# ═══════════════════════════════════════════════════════════════════════

@tool
def vercel_login() -> str:
    """Log into Vercel CLI. Clears any stale credentials first, then opens
    your browser for OAuth authorization. Uses npx so no global install needed.

    Returns:
        str: Login result with username/email.
    """
    _console.print(Panel(
        "[bold]Initiating Vercel CLI login...[/bold]",
        title="[bold blue]🔐 Vercel Login[/bold blue]",
        border_style="blue",
    ))

    # Always clear old creds when explicitly logging in
    _force_clear_credentials()

    err = _ensure_logged_in()
    if err:
        return f"❌ {err}"

    user = _get_vercel_user()
    return f"✅ Logged into Vercel as {user}"


@tool
def vercel_logout() -> str:
    """Log out of Vercel CLI. Clears ALL stored credentials including
    cached auth files, so you can log in with a different account.

    Returns:
        str: Logout result.
    """
    user = _get_vercel_user()

    _console.print(Panel(
        f"[bold yellow]Logging out of Vercel CLI...[/bold yellow]\n\n"
        f"[dim]Current user: {user}\n"
        f"Clearing all stored Vercel tokens and auth files.[/dim]",
        title="[bold blue]🔓 Vercel Logout[/bold blue]",
        border_style="yellow",
        padding=(1, 2),
    ))

    _force_clear_credentials()

    # Verify actually logged out
    check = _cmd(f"{VERCEL} whoami", timeout=30)
    if not check["ok"]:
        _console.print(f"[bold green]✅ Logged out from Vercel ({user})[/bold green]")
        return f"✅ Logged out of Vercel (was {user}). All credentials cleared."
    else:
        _console.print(f"[bold red]⚠ May still be logged in[/bold red]")
        return f"⚠ Logout may have failed — still showing as {check['out']}"


@tool
def vercel_deploy(project_dir: str, production: bool = False) -> str:
    """Deploy a project to Vercel with FULL automation. NO extra confirmation
    needed — just call this tool and it handles everything:
    - Uses npx (no global install needed)
    - If not logged in → opens browser for OAuth login
    - Deploys as a NEW project (avoids access/permission issues)
    - Opens the live URL in your browser

    Args:
        project_dir: Path to the project directory to deploy.
        production: If True, deploy to production. If False, preview deployment.

    Returns:
        str: Deployment URL or error message.
    """
    if not os.path.isdir(project_dir):
        return f"ERROR: Directory not found: {project_dir}"

    deploy_type = "PRODUCTION" if production else "PREVIEW"

    _console.print(Panel(
        f"[bold]Directory:[/bold]  {project_dir}\n"
        f"[bold]Type:[/bold]       {deploy_type}\n"
        f"[bold]Platform:[/bold]   Vercel (via npx)",
        title=f"[bold blue]🚀 Vercel Deploy ({deploy_type})[/bold blue]",
        border_style="blue",
        padding=(0, 2),
    ))

    # Step 1: Ensure logged in (opens browser if needed)
    _console.print("\n[bold]Step 1/2:[/bold] Checking authentication...")
    err = _ensure_logged_in()
    if err:
        return f"❌ {err}"

    # Step 2: Deploy — NO confirmation needed, user already approved
    _console.print(f"[bold]Step 2/2:[/bold] Deploying to Vercel ({deploy_type})...")
    _console.print("[dim]⏳ This may take a minute...[/dim]")

    # --yes: accept defaults, skip prompts
    # --force: create new deployment even if project exists
    # This avoids "requesting access" issues from old team deployments
    cmd = f"{VERCEL} --yes"
    if production:
        cmd += " --prod"

    # Remove any existing .vercel folder to force fresh project link
    vercel_dir = os.path.join(project_dir, ".vercel")
    if os.path.isdir(vercel_dir):
        _console.print("[dim]  Removing old .vercel project link...[/dim]")
        import shutil
        shutil.rmtree(vercel_dir, ignore_errors=True)

    r = _cmd(cmd, cwd=project_dir, timeout=300)

    if r["ok"]:
        # Last line of output is the URL
        lines = r["out"].strip().split("\n")
        url = lines[-1].strip()
        if url.startswith("http"):
            _console.print(Panel(
                f"[bold green]✅ Deployed successfully![/bold green]\n\n"
                f"[bold]🌐 URL:[/bold]  {url}\n"
                f"[bold]📋 Type:[/bold] {deploy_type}\n"
                f"[bold]🔗 Opening in browser...[/bold]",
                title="[bold green]Deployment Complete[/bold green]",
                border_style="green",
                padding=(1, 2),
            ))
            webbrowser.open(url)
            return f"✅ Deployed!\n🌐 URL: {url}\nType: {deploy_type}\n(Opened in browser)"
        _console.print(f"[green]✅ Deployed![/green]\n[dim]Output: {r['out'][:500]}[/dim]")
        return f"✅ Deployed!\nOutput: {r['out'][:1000]}"
    else:
        err_msg = r["err"] or r["out"]
        _console.print(Panel(
            f"[bold red]❌ Deployment failed[/bold red]\n\n"
            f"[dim]{err_msg[:500]}[/dim]",
            title="[bold red]Deploy Error[/bold red]",
            border_style="red",
            padding=(1, 2),
        ))
        return f"❌ Deploy failed:\n{err_msg[:1500]}"


@tool
def vercel_status(project_dir: str) -> str:
    """Check recent Vercel deployments for a project.

    Args:
        project_dir: Path to the project directory.

    Returns:
        str: Recent deployments list.
    """
    _console.print("[dim]📋 Fetching recent deployments...[/dim]")
    r = _cmd(f"{VERCEL} ls --limit 5", cwd=project_dir)
    if r["ok"]:
        _console.print(Panel(
            f"[white]{r['out'][:1000]}[/white]",
            title="[bold blue]Recent Vercel Deployments[/bold blue]",
            border_style="blue",
            padding=(0, 2),
        ))
        return r["out"]
    return f"ERROR: {r['err']}"


@tool
def vercel_env_set(project_dir: str, key: str, value: str) -> str:
    """Set an environment variable on Vercel.

    Args:
        project_dir: Project directory path.
        key: Env var name.
        value: Env var value.

    Returns:
        str: Result message.
    """
    _console.print(f"[dim]🔧 Setting env var '{key}'...[/dim]")
    r = _cmd(f'echo "{value}" | {VERCEL} env add {key} production', cwd=project_dir)
    if r["ok"]:
        _console.print(f"[green]✓[/green] Set {key}")
        return f"✅ Set {key}"
    _console.print(f"[red]❌ Failed to set {key}[/red]")
    return f"❌ {r['err']}"


VERCEL_TOOLS = [vercel_login, vercel_logout, vercel_deploy, vercel_status, vercel_env_set]
