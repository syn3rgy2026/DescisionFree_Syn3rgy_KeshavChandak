import os
from dotenv import load_dotenv

load_dotenv()

# ── InferX LLM Configuration ──────────────────────────────────────────
INFERX_ENDPOINT = os.getenv("INFERX_ENDPOINT", "")
INFERX_API_KEY  = os.getenv("INFERX_API_KEY", "")
MODEL_ID        = os.getenv("MODEL_ID", "google/gemma-4-31B-it")

# ── Folder Paths ──────────────────────────────────────────────────────
SKILLS_FOLDER   = "./skills/"
PROMPTS_FOLDER  = "./agent/prompts/"
# Default folder for artefacts when the user does not name Desktop/home/path (see master prompt).
OUTPUT_FOLDER   = "./output/"

# ── Agent Limits ──────────────────────────────────────────────────────
MAX_STEPS       = 15
SHELL_TIMEOUT   = 30

# LLM HTTP retries (502/503, timeouts, empty JSON from proxies — see agent/resilient_llm.py)
MODEL_RETRY_MAX_ATTEMPTS = int(os.getenv("MODEL_RETRY_MAX_ATTEMPTS", "5"))
MODEL_RETRY_WAIT_SEC     = float(os.getenv("MODEL_RETRY_WAIT_SEC", "2"))

# Full agent.run() retries after the model exhausts its own retries (fresh run)
AGENT_RUN_MAX_RETRIES = int(os.getenv("AGENT_RUN_MAX_RETRIES", "3"))
