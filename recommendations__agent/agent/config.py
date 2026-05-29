import os                                            # Read environment variables
from dotenv import load_dotenv                       # Load .env file into os.environ

from openai import AsyncOpenAI                       # OpenAI-compatible HTTP client
from agents import (                                 # OpenAI Agents SDK
    set_default_openai_client,                       #   Make Gemini the default LLM
    set_tracing_export_api_key,                      #   Forward traces to OpenAI dashboard
    OpenAIChatCompletionsModel,                      #   Wrapper that speaks the OpenAI protocol
)

load_dotenv()                                        # Read variables from .env file

# ── Environment variables ──────────────────────────────────────────────────────
# These are set in the .env file at the project root.
GEMINI_API_KEY     = os.getenv("GROQ_API_KEY", "")   # Gemini API key
GEMINI_BASE_URL    = os.getenv("GROQ_BASE_URL", "")  # Gemini-compatible endpoint
MODEL_NAME         = os.getenv("GROQ_MODEL", "")     # e.g. "gemini-2.5-flash"
OPENAI_TRACING_KEY = os.getenv("OPENAI_API_KEY", "sk-proj-your-openai-key-here")

_gemini_client: AsyncOpenAI | None = None            # Cached HTTP client (lazy init)


def get_gemini_client() -> AsyncOpenAI:
    """Return a singleton AsyncOpenAI client pointed at the Gemini API."""
    global _gemini_client
    if _gemini_client is None:                       # Create client once
        _gemini_client = AsyncOpenAI(
            api_key=GEMINI_API_KEY,
            base_url=GEMINI_BASE_URL,
        )
    return _gemini_client


def init_gemini_client():
    """Make Gemini the default LLM provider and configure tracing."""
    client = get_gemini_client()
    set_default_openai_client(client, use_for_tracing=False)  # Use Gemini for LLM calls
    set_tracing_export_api_key(OPENAI_TRACING_KEY)            # Enable OpenAI dashboard export
    os.environ["OPENAI_API_KEY"] = OPENAI_TRACING_KEY         # SDK checks this env var


def get_model() -> OpenAIChatCompletionsModel:
    """Return an OpenAIChatCompletionsModel that routes through Gemini."""
    return OpenAIChatCompletionsModel(
        model=MODEL_NAME,
        openai_client=get_gemini_client(),
    )
