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
OUTPUT_FOLDER   = "./output/"

# ── Agent Limits ──────────────────────────────────────────────────────
MAX_STEPS       = 15
SHELL_TIMEOUT   = 30
