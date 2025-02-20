import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parents[2] / ".env"
load_dotenv(env_path)
print(env_path)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
