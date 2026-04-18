import os
from dotenv import load_dotenv

load_dotenv()

INFERX_ENDPOINT = os.getenv("INFERX_ENDPOINT", "https://placeholder-endpoint.com")
INFERX_API_KEY  = os.getenv("INFERX_API_KEY", "placeholder-key")
MODEL_ID        = os.getenv("MODEL_ID", "google/gemma-4-31B-it")

SKILLS_FOLDER   = "./skills/"
MEMORY_FOLDER   = "./memory/"
PROMPTS_FOLDER  = "./agent/prompts/"
OUTPUT_FOLDER   = "./output/"

MAX_STEPS       = 20
SHELL_TIMEOUT   = 30
