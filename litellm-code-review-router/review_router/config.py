"""Settings: which models to compare and where the sample diffs live."""

import os
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

# Walk up from here to find a .env (this folder's own, or a repo-root one).
load_dotenv(find_dotenv(usecwd=False))

# Some dev environments point Anthropic traffic at a local proxy; LiteLLM must reach the real API.
os.environ.pop("ANTHROPIC_BASE_URL", None)

# LiteLLM model strings: "<provider>/<model>". Adding a model here is the only change a new provider needs.
DEFAULT_MODELS = [
    "openai/gpt-4o-mini",
    "anthropic/claude-haiku-4-5-20251001",
]

PROJECT_NAME = "litellm-code-review-router"

DIFFS_DIR = Path(__file__).resolve().parent.parent / "data" / "diffs"
