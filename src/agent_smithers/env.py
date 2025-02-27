import os
from pathlib import Path

from dotenv import load_dotenv

env_path = Path(__file__).parents[2] / ".env"
load_dotenv(env_path)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
