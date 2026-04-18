import sys

from tools.file_tool import ALL_TOOLS as FILE_TOOLS
from tools.shell_tool import SHELL_TOOLS
from tools.email_tool import send_email, reset_email_credentials
from tools.email_reader_tool import read_emails

EMAIL_TOOLS = [send_email, reset_email_credentials, read_emails]

# ── Memory tools (SQLite only — no ChromaDB) ─────────────────────────
try:
    from memory.working import WorkingMemoryTool
    from memory.persistent import PersistentMemoryTool
    MEMORY_TOOLS = [WorkingMemoryTool(), PersistentMemoryTool()]
except Exception as _mem_err:
    print(f"⚠️  Memory tools failed to load: {_mem_err}", file=sys.stderr)
    MEMORY_TOOLS = []

# ── Browser tools (Playwright) ────────────────────────────────────────
# ── Browser tools (Playwright + Visit tool) ───────────────────────────
try:
    from tools.browser_tool import BROWSER_TOOLS as PLAYWRIGHT_TOOLS
except Exception as _e:
    print(f"⚠️  Browser tools failed to load: {_e}", file=sys.stderr)
    PLAYWRIGHT_TOOLS = []

try:
    from tools.visit_tool import visit_url, get_page_links, fill_and_submit_form
    VISIT_TOOLS = [visit_url, get_page_links, fill_and_submit_form]
except Exception as _e:
    print(f"⚠️  Visit tools failed to load: {_e}", file=sys.stderr)
    VISIT_TOOLS = []

BROWSER_TOOLS = PLAYWRIGHT_TOOLS + VISIT_TOOLS

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

# ── File watcher tools ────────────────────────────────────────────────
try:
    from tools.file_watcher import detect_new_images
    FILE_WATCHER_TOOLS = [detect_new_images]
except Exception as _e:
    print(f"⚠️  File watcher tools failed to load: {_e}", file=sys.stderr)
    FILE_WATCHER_TOOLS = []

# ── Instagram tools ───────────────────────────────────────────────────
try:
    from tools.instagram_tool import post_to_instagram, login_to_instagram
    INSTAGRAM_TOOLS = [post_to_instagram, login_to_instagram]
except Exception as _e:
    print(f"⚠️  Instagram tools failed to load: {_e}", file=sys.stderr)
    INSTAGRAM_TOOLS = []

# ── LinkedIn tools ────────────────────────────────────────────────────
try:
    from tools.linkedin_tool import post_to_linkedin, login_to_linkedin
    LINKEDIN_TOOLS = [post_to_linkedin, login_to_linkedin]
except Exception as _e:
    print(f"⚠️  LinkedIn tools failed to load: {_e}", file=sys.stderr)
    LINKEDIN_TOOLS = []

# ── PowerPoint tools ──────────────────────────────────────────────────
try:
    from tools.ppt_tool import PPT_TOOLS
except Exception as _e:
    print(f"⚠️  PPT tools failed to load: {_e}", file=sys.stderr)
    PPT_TOOLS = []

# ── Live data tools (cricket, weather, stocks, crypto, news, fx) ──────
try:
    from tools.live_data_tools import LIVE_DATA_TOOLS
except Exception as _e:
    print(f"⚠️  Live data tools failed to load: {_e}", file=sys.stderr)
    LIVE_DATA_TOOLS = []

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
    + FILE_WATCHER_TOOLS
    + INSTAGRAM_TOOLS
    + LINKEDIN_TOOLS
    + PPT_TOOLS
    + LIVE_DATA_TOOLS
)
