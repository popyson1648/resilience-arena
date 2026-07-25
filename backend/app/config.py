"""Environment configuration. The Gemini API key stays server-side only."""

import os

from dotenv import load_dotenv

load_dotenv()

GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")
RUN_TIMEOUT_SECONDS = int(os.environ.get("RUN_TIMEOUT_SECONDS", "120"))
MAX_LLM_CALLS = int(os.environ.get("MAX_LLM_CALLS", "15"))
FRONTEND_DIST = os.environ.get("FRONTEND_DIST", "../frontend/dist")
