import os
import asyncio
import logging
from dotenv import load_dotenv

from openai import AsyncOpenAI
from agents import (
    set_default_openai_client,
    set_tracing_export_api_key,
    OpenAIChatCompletionsModel,
)

load_dotenv()

logger = logging.getLogger(__name__)

# ── OpenRouter (all models) ──────────────────────────────────────────────────
OPENROUTER_API_KEY           = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL          = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTER_MODEL_PRIMARY     = os.getenv("OPENROUTER_MODEL_PRIMARY", "google/gemini-2.0-flash-001:free")
OPENROUTER_MODEL_FALLBACK_1  = os.getenv("OPENROUTER_MODEL_FALLBACK_1", "moonshotai/kimi-k2.6:free")
OPENROUTER_MODEL_FALLBACK_2  = os.getenv("OPENROUTER_MODEL_FALLBACK_2", "openai/gpt-oss-120b:free")
OPENROUTER_MODEL_FALLBACK_3  = os.getenv("OPENROUTER_MODEL_FALLBACK_3", "openai/gpt-oss-20b:free")
OPENROUTER_MODEL_FALLBACK_4  = os.getenv("OPENROUTER_MODEL_FALLBACK_4", "qwen/qwen3-next-80b-a3b-instruct:free")

# ── RapidAPI ────────────────────────────────────────────────────────────────
RAPIDAPI_KEY  = os.getenv("RAPIDAPI_KEY", "")
RAPIDAPI_HOST = os.getenv("RAPIDAPI_HOST", "real-time-amazon-data.p.rapidapi.com")

# ── Qdrant ──────────────────────────────────────────────────────────────────
QDRANT_URL     = os.getenv("QDRANT_URL", "")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")

# ── Tracing ─────────────────────────────────────────────────────────────────
OPENAI_TRACING_KEY = os.getenv("OPENAI_API_KEY", "")

# ── Retry / fallback settings ────────────────────────────────────────────────
MAX_RETRIES        = 3
BASE_BACKOFF_SECS  = 1.0
BACKOFF_MULTIPLIER = 2.0

# ── Clients (lazy) ──────────────────────────────────────────────────────────
_openrouter_client: AsyncOpenAI | None = None

_active_model_name: str = ""


def get_openrouter_client() -> AsyncOpenAI:
    global _openrouter_client
    if _openrouter_client is None:
        _openrouter_client = AsyncOpenAI(
            api_key=OPENROUTER_API_KEY,
            base_url=OPENROUTER_BASE_URL,
        )
    return _openrouter_client


def init_clients():
    """Configure default client + tracing (called once at startup)."""
    client = get_openrouter_client()
    set_default_openai_client(client, use_for_tracing=False)
    set_tracing_export_api_key(OPENAI_TRACING_KEY)
    os.environ["OPENAI_API_KEY"] = OPENAI_TRACING_KEY


def _build_model(model_id: str) -> tuple[OpenAIChatCompletionsModel, str]:
    label = f"openrouter/{model_id}"
    return OpenAIChatCompletionsModel(model=model_id, openai_client=get_openrouter_client()), label


def get_model() -> OpenAIChatCompletionsModel:
    """Return the primary model (Gemini 2.0 Flash)."""
    global _active_model_name
    model, label = _build_model(OPENROUTER_MODEL_PRIMARY)
    _active_model_name = label
    return model


def get_fallback_model() -> OpenAIChatCompletionsModel:
    """Return the first fallback model (Kimi K2.6)."""
    global _active_model_name
    model, label = _build_model(OPENROUTER_MODEL_FALLBACK_1)
    _active_model_name = label
    return model


def get_deep_fallback_model() -> OpenAIChatCompletionsModel:
    """Return the second fallback model (gpt-oss-120b)."""
    global _active_model_name
    model, label = _build_model(OPENROUTER_MODEL_FALLBACK_2)
    _active_model_name = label
    return model


def get_fallback_3_model() -> OpenAIChatCompletionsModel:
    """Return the third fallback model (gpt-oss-20b)."""
    global _active_model_name
    model, label = _build_model(OPENROUTER_MODEL_FALLBACK_3)
    _active_model_name = label
    return model


def get_fallback_4_model() -> OpenAIChatCompletionsModel:
    """Return the fourth fallback model (qwen3-next-80b)."""
    global _active_model_name
    model, label = _build_model(OPENROUTER_MODEL_FALLBACK_4)
    _active_model_name = label
    return model


def active_model_name() -> str:
    return _active_model_name


# ── Retry helper ────────────────────────────────────────────────────────────
async def run_with_retry(coro_factory, max_retries: int = MAX_RETRIES):
    """Await a coroutine with exponential-backoff retry.

    coro_factory — a zero-arg callable that returns a coroutine.
    Returns (result, model_label) on success.
    Raises the last exception if all retries fail.
    """
    last_exc = None
    for attempt in range(max_retries):
        try:
            result = await coro_factory()
            return result, active_model_name()
        except Exception as exc:
            last_exc = exc
            logger.warning("Retry %d/%d failed: %s", attempt + 1, max_retries, exc)
            if attempt + 1 < max_retries:
                wait = BASE_BACKOFF_SECS * (BACKOFF_MULTIPLIER ** attempt)
                await asyncio.sleep(wait)
    raise last_exc
