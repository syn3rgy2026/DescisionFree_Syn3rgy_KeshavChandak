import os
from dotenv import load_dotenv

load_dotenv()

# ── InferX LLM Configuration ──────────────────────────────────────────
INFERX_ENDPOINT = os.getenv("INFERX_ENDPOINT", "https://litellm-proxy-93ef.onrender.com/v1/chat/completions")
INFERX_API_KEY  = os.getenv("INFERX_API_KEY", "sk-xC1fI8kctncMU7EunUyCYQ")
MODEL_ID        = os.getenv("MODEL_ID", "google/gemma-4-31B-it")

# ── Folder Paths ──────────────────────────────────────────────────────
SKILLS_FOLDER   = "./skills/"
PROMPTS_FOLDER  = "./agent/prompts/"
OUTPUT_FOLDER   = "./output/"

# ── Agent Limits ──────────────────────────────────────────────────────
MAX_STEPS       = 20
SHELL_TIMEOUT   = 30
