import sys

from tools.file_tool import ALL_TOOLS as FILE_TOOLS
from tools.shell_tool import SHELL_TOOLS
from tools.email_tool import send_email, reset_email_credentials
from tools.email_reader_tool import read_emails

EMAIL_TOOLS = [send_email, reset_email_credentials, read_emails]

# ── Memory tools ──────────────────────────────────────────────────────
try:
    from memory.working import WorkingMemoryTool
    from memory.persistent import PersistentMemoryTool
    from memory.semantic import SemanticMemoryTool
    MEMORY_TOOLS = [WorkingMemoryTool(), PersistentMemoryTool(), SemanticMemoryTool()]
except Exception as _e:
    print(f"⚠️  Memory tools failed to load: {_e}", file=sys.stderr)
    MEMORY_TOOLS = []

# ── Browser tools (Playwright) ────────────────────────────────────────
try:
    from tools.browser_tool import BROWSER_TOOLS
except Exception as _e:
    print(f"⚠️  Browser tools failed to load: {_e}", file=sys.stderr)
    BROWSER_TOOLS = []

# ── Code runner / debugger tools ──────────────────────────────────────
try:
    from tools.code_runner_tool import CODE_RUNNER_TOOLS
except Exception as _e:
    print(f"⚠️  Code runner tools failed to load: {_e}", file=sys.stderr)
    CODE_RUNNER_TOOLS = []

# ── Dev server tools ──────────────────────────────────────────────────
try:
    from tools.dev_server_tool import DEV_SERVER_TOOLS
except Exception as _e:
    print(f"⚠️  Dev server tools failed to load: {_e}", file=sys.stderr)
    DEV_SERVER_TOOLS = []

# ── Vercel deployment tools ───────────────────────────────────────────
try:
    from tools.vercel_deploy_tool import VERCEL_TOOLS
except Exception as _e:
    print(f"⚠️  Vercel tools failed to load: {_e}", file=sys.stderr)
    VERCEL_TOOLS = []

# ── GitHub tools ──────────────────────────────────────────────────────
try:
    from tools.github_tool import GITHUB_TOOLS
except Exception as _e:
    print(f"⚠️  GitHub tools failed to load: {_e}", file=sys.stderr)
    GITHUB_TOOLS = []

ALL_TOOLS = (
    FILE_TOOLS
    + SHELL_TOOLS
    + EMAIL_TOOLS
    + MEMORY_TOOLS
    + BROWSER_TOOLS
    + CODE_RUNNER_TOOLS
    + DEV_SERVER_TOOLS
    + VERCEL_TOOLS
    + GITHUB_TOOLS
)
