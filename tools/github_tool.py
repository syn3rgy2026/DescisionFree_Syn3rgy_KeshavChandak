"""
github_tool.py
--------------
GitHub integration: create repos, push code, manage repos.
Full automated flow:
  1. Checks if GitHub CLI (gh) is installed (installs if not)
  2. Checks if logged in (interactive OAuth device flow if not)
  3. Creates repo / pushes code
  4. Opens the repo URL in browser

Authentication uses subprocess with INHERITED stdin/stdout/stderr
so the gh CLI's OAuth device-code flow runs interactively in the
user's terminal — browser opens, user authorizes, token saved.
"""

import os
import subprocess
import webbrowser
from smolagents import tool
from rich.console import Console
from rich.panel import Panel

_console = Console()


def _cmd(cmd: str, cwd: str = ".", timeout: int = 120) -> dict:
    """Run a shell command and capture output."""
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                           timeout=timeout, cwd=cwd)
        return {"ok": r.returncode == 0, "out": r.stdout.strip(), "err": r.stderr.strip()}
    except subprocess.TimeoutExpired:
        return {"ok": False, "out": "", "err": f"TIMEOUT ({timeout}s)"}
    except Exception as e:
        return {"ok": False, "out": "", "err": str(e)}


def _ensure_gh_cli() -> str | None:
    """Ensure GitHub CLI is installed. Returns error or None."""
    r = _cmd("gh --version", timeout=10)
    if r["ok"]:
        _console.print("[green]✓[/green] GitHub CLI detected")
        return None

    _console.print(Panel(
        "[yellow]GitHub CLI (gh) not found — installing...[/yellow]",
        title="[bold blue]📦 Installing GitHub CLI[/bold blue]",
        border_style="blue",
    ))

    # Try installing via brew (macOS)
    code = os.system("brew install gh 2>/dev/null")
    r = _cmd("gh --version", timeout=10)
    if r["ok"]:
        _console.print("[green]✓[/green] GitHub CLI installed successfully")
        return None
    return "GitHub CLI (gh) not installed. Install it: brew install gh"


def _ensure_gh_logged_in() -> str | None:
    """
    Ensure logged into GitHub. If not, open an interactive OAuth device flow
    in the user's terminal with full TTY passthrough.
    """
    _console.print("[dim]🔑 Checking GitHub authentication...[/dim]")

    r = _cmd("gh auth status", timeout=15)
    if r["ok"]:
        # Extract username from status
        username = _get_gh_user()
        _console.print(f"[green]✓[/green] Authenticated as [bold cyan]@{username}[/bold cyan]")
        return None

    # Not logged in → clear stale creds and do interactive login
    _console.print(Panel(
        "[bold yellow]You are not logged into GitHub.[/bold yellow]\n\n"
        "[white]An interactive login flow will start NOW in your terminal.[/white]\n\n"
        "[bold cyan]What will happen:[/bold cyan]\n"
        "[dim]  1. A one-time device code will be displayed\n"
        "  2. Your browser will open to github.com/login/device\n"
        "  3. Paste the code and authorize the app\n"
        "  4. Return here — you'll be logged in automatically[/dim]\n\n"
        "[bold green]>>> Follow the prompts below <<<[/bold green]",
        title="[bold blue]🌐 GitHub OAuth Login Required[/bold blue]",
        border_style="yellow",
        padding=(1, 2),
    ))

    _console.print("[bold cyan]⏳ Starting GitHub login now...[/bold cyan]\n")

    # Use os.system() — this directly inherits the real terminal's
    # stdin/stdout/stderr file descriptors, which works correctly
    # even when called from inside smolagents' CodeAgent sandbox.
    # subprocess.run with sys.stdin does NOT work in that context.
    exit_code = os.system("gh auth login --web --git-protocol https")

    if exit_code != 0:
        _console.print("\n[bold red]❌ GitHub login failed or was cancelled.[/bold red]")
        _console.print("[dim]Try running 'gh auth login' manually in a separate terminal.[/dim]")
        return "GitHub login failed. Try running 'gh auth login' manually in your terminal."

    # Verify login succeeded
    r = _cmd("gh auth status", timeout=15)
    if r["ok"]:
        username = _get_gh_user()
        _console.print(f"\n[bold green]✅ Successfully authenticated as @{username}[/bold green]")
        return None

    return "Still not authenticated after login attempt. Try 'gh auth login' manually."


def _ensure_git_init(project_dir: str) -> None:
    """Initialize git repo if not already one."""
    r = _cmd("git rev-parse --is-inside-work-tree", cwd=project_dir)
    if not r["ok"]:
        _console.print(f"[dim]📁 Initializing git repo in {project_dir}...[/dim]")
        _cmd("git init", cwd=project_dir)
        _cmd("git add -A", cwd=project_dir)
        _cmd('git commit -m "Initial commit"', cwd=project_dir)
        _console.print("[green]✓[/green] Git repo initialized with initial commit")


def _get_gh_user() -> str:
    """Get the current GitHub username."""
    r = _cmd("gh api user --jq '.login'", timeout=10)
    return r["out"] if r["ok"] else "unknown"


# ═══════════════════════════════════════════════════════════════════════
#  Public tools
# ═══════════════════════════════════════════════════════════════════════

@tool
def github_create_and_push(project_dir: str, repo_name: str, private: bool = False, description: str = "") -> str:
    """Create a GitHub repo and push your project to it. Full automation:
    - If gh CLI missing → installs it
    - If not logged in → opens browser for GitHub OAuth (you authorize, done)
    - Creates the repo on your GitHub account
    - Pushes all code
    - Opens the repo in your browser

    Args:
        project_dir: Path to the project directory to push.
        repo_name: Name for the GitHub repository (e.g. 'my-todo-app').
        private: If True, create private repo. Default is public.
        description: Optional repo description.

    Returns:
        str: GitHub repo URL or error message.
    """
    if not os.path.isdir(project_dir):
        return f"ERROR: Directory not found: {project_dir}"

    _console.print(Panel(
        f"[bold]Repo:[/bold]  {repo_name}\n"
        f"[bold]From:[/bold]  {project_dir}\n"
        f"[bold]Type:[/bold]  {'PRIVATE' if private else 'PUBLIC'}",
        title="[bold blue]🚀 GitHub Create & Push[/bold blue]",
        border_style="blue",
        padding=(0, 2),
    ))

    # Step 1: Ensure gh CLI
    _console.print("\n[bold]Step 1/5:[/bold] Checking GitHub CLI...")
    err = _ensure_gh_cli()
    if err:
        return f"❌ {err}"

    # Step 2: Ensure logged in (opens browser if needed)
    _console.print("[bold]Step 2/5:[/bold] Checking authentication...")
    err = _ensure_gh_logged_in()
    if err:
        return f"❌ {err}"

    # Step 3: Init git if needed
    visibility = "PRIVATE" if private else "PUBLIC"
    _console.print("[bold]Step 3/4:[/bold] Preparing git repo...")
    _ensure_git_init(project_dir)

    # Make sure all files are staged
    _cmd("git add -A", cwd=project_dir)
    r = _cmd("git status --short", cwd=project_dir)
    if r["out"]:
        _cmd('git commit -m "Update before push"', cwd=project_dir)

    # Step 4: Create repo and push — NO confirmation needed, user already approved
    _console.print(f"[bold]Step 4/4:[/bold] Creating repo and pushing code...")
    vis_flag = "--private" if private else "--public"
    desc_flag = f'--description "{description}"' if description else ""
    cmd = f'gh repo create {repo_name} {vis_flag} {desc_flag} --source=. --remote=origin --push'

    r = _cmd(cmd, cwd=project_dir, timeout=60)

    if r["ok"]:
        repo_url = f"https://github.com/{_get_gh_user()}/{repo_name}"
        _console.print(Panel(
            f"[bold green]✅ Repository created and code pushed![/bold green]\n\n"
            f"[bold]🔗 URL:[/bold]  {repo_url}\n"
            f"[bold]👁 Visibility:[/bold] {visibility}\n"
            f"[bold]🌐 Opening in browser...[/bold]",
            title="[bold green]Success[/bold green]",
            border_style="green",
            padding=(1, 2),
        ))
        webbrowser.open(repo_url)
        return f"✅ Repo created and code pushed!\n🔗 URL: {repo_url}\nVisibility: {visibility}\n(Opened in browser)"
    else:
        err_msg = r["err"] or r["out"]
        if "already exists" in err_msg.lower():
            _console.print("[yellow]⚠ Repo already exists — use github_push instead.[/yellow]")
            return f"Repo '{repo_name}' already exists. Use github_push to push to it."
        _console.print(f"[bold red]❌ Failed to create repo:[/bold red]\n{err_msg[:500]}")
        return f"❌ Failed:\n{err_msg[:1500]}"


@tool
def github_push(project_dir: str, message: str = "Update", branch: str = "main") -> str:
    """Stage all changes, commit, and push to the existing GitHub remote.

    Args:
        project_dir: Path to the project directory.
        message: Commit message.
        branch: Branch to push to (default: main).

    Returns:
        str: Push result.
    """
    if not os.path.isdir(project_dir):
        return f"ERROR: Directory not found: {project_dir}"

    _console.print(Panel(
        f"[bold]Dir:[/bold]     {project_dir}\n"
        f"[bold]Branch:[/bold]  {branch}\n"
        f"[bold]Message:[/bold] {message}",
        title="[bold blue]📤 Git Push[/bold blue]",
        border_style="blue",
        padding=(0, 2),
    ))

    _console.print("[dim]🔑 Checking authentication...[/dim]")
    err = _ensure_gh_logged_in()
    if err:
        return f"❌ {err}"

    cmds = [
        ("Staging files...", "git add -A"),
        ("Committing...", f'git commit -m "{message}"'),
        ("Pushing...", f"git push origin {branch}"),
    ]
    for label, c in cmds:
        _console.print(f"[dim]  → {label}[/dim]")
        r = _cmd(c, cwd=project_dir)
        if not r["ok"] and "nothing to commit" not in (r["err"] + r["out"]):
            _console.print(f"[bold red]❌ Failed on '{c}'[/bold red]")
            return f"❌ Failed on '{c}':\n{r['err'] or r['out']}"

    _console.print(f"[bold green]✅ Pushed to {branch}[/bold green]")
    return f"✅ Pushed to {branch} with message: '{message}'"


@tool
def github_clone(repo_url: str, target_dir: str = "") -> str:
    """Clone a GitHub repository.

    Args:
        repo_url: Full repo URL or owner/repo shorthand (e.g. 'vercel/next.js').
        target_dir: Optional directory to clone into.

    Returns:
        str: Clone result.
    """
    _console.print(Panel(
        f"[bold]Repo:[/bold]   {repo_url}\n"
        f"[bold]Target:[/bold] {target_dir or '(default)'}",
        title="[bold blue]📥 Git Clone[/bold blue]",
        border_style="blue",
        padding=(0, 2),
    ))

    err = _ensure_gh_cli()
    if err:
        return f"❌ {err}"

    cmd = f"gh repo clone {repo_url}"
    if target_dir:
        cmd += f" {target_dir}"

    _console.print("[dim]⏳ Cloning repository...[/dim]")
    r = _cmd(cmd, timeout=120)
    if r["ok"]:
        _console.print(f"[bold green]✅ Cloned {repo_url}[/bold green]")
        return f"✅ Cloned {repo_url}"
    _console.print(f"[bold red]❌ Clone failed[/bold red]")
    return f"❌ Clone failed:\n{r['err'] or r['out']}"


@tool
def github_status() -> str:
    """Check your current GitHub authentication status.
    Shows whether you're logged in, your username, and auth method.

    Returns:
        str: Authentication status details.
    """
    _console.print("[dim]🔑 Checking GitHub auth status...[/dim]")

    r = _cmd("gh auth status", timeout=15)
    if r["ok"]:
        username = _get_gh_user()
        status_text = r["out"] or r["err"]  # gh auth status prints to stderr
        _console.print(Panel(
            f"[bold green]✅ Logged in as @{username}[/bold green]\n\n"
            f"[dim]{status_text[:500]}[/dim]",
            title="[bold blue]GitHub Auth Status[/bold blue]",
            border_style="green",
            padding=(1, 2),
        ))
        return f"✅ Logged in as @{username}\n\n{status_text[:500]}"
    else:
        status_text = r["err"] or r["out"]
        _console.print(Panel(
            f"[bold red]❌ Not logged in[/bold red]\n\n"
            f"[dim]{status_text[:500]}[/dim]\n\n"
            "[yellow]Use any GitHub tool and it will automatically prompt you to log in,[/yellow]\n"
            "[yellow]or run 'gh auth login' manually in your terminal.[/yellow]",
            title="[bold blue]GitHub Auth Status[/bold blue]",
            border_style="red",
            padding=(1, 2),
        ))
        return f"❌ Not logged in.\n{status_text[:500]}\n\nUse a GitHub tool to trigger automatic login."


@tool
def github_logout() -> str:
    """Log out of GitHub CLI. Clears stored credentials so you can log in
    with a different account next time.

    Returns:
        str: Logout result.
    """
    _console.print(Panel(
        "[bold yellow]Logging out of GitHub CLI...[/bold yellow]\n\n"
        "[dim]This clears your stored GitHub token.\n"
        "You will need to re-authenticate next time you use a GitHub tool.[/dim]",
        title="[bold blue]🔓 GitHub Logout[/bold blue]",
        border_style="yellow",
        padding=(1, 2),
    ))

    # Get current user before logging out
    username = _get_gh_user()

    # gh auth logout — use os.system for interactive TTY
    exit_code = os.system("gh auth logout --hostname github.com 2>/dev/null")
    r = {"ok": exit_code == 0, "out": "", "err": ""}

    # If that didn't work (maybe needs confirmation), force it
    if not r["ok"]:
        try:
            result = subprocess.run(
                ["gh", "auth", "logout", "--hostname", "github.com"],
                input="Y\n",
                capture_output=True,
                text=True,
                timeout=15,
            )
            r = {"ok": result.returncode == 0, "out": result.stdout, "err": result.stderr}
        except Exception as e:
            r = {"ok": False, "out": "", "err": str(e)}

    if r["ok"] or "not logged" in (r["err"] + r["out"]).lower():
        _console.print(f"[bold green]✅ Logged out from @{username}[/bold green]")
        return f"✅ Logged out of GitHub (was @{username}). Credentials cleared."
    else:
        _console.print(f"[bold red]❌ Logout issue:[/bold red] {r['err'][:300]}")
        return f"⚠ Logout may have failed: {r['err'][:300]}"


GITHUB_TOOLS = [github_create_and_push, github_push, github_clone, github_status, github_logout]
