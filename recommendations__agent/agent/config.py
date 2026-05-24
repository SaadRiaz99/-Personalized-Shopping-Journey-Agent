import os
from dotenv import load_dotenv

from openai import AsyncOpenAI
from agents import (
    set_default_openai_client,
    OpenAIChatCompletionsModel,
)

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
MODEL_NAME = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

_groq_client: AsyncOpenAI | None = None


def get_groq_client() -> AsyncOpenAI:
    global _groq_client
    if _groq_client is None:
        _groq_client = AsyncOpenAI(
            api_key=GROQ_API_KEY,
            base_url=GROQ_BASE_URL,
        )
    return _groq_client


def init_groq_client():
    client = get_groq_client()
    set_default_openai_client(client, use_for_tracing=False)


def get_model() -> OpenAIChatCompletionsModel:
    return OpenAIChatCompletionsModel(
        model=MODEL_NAME,
        openai_client=get_groq_client(),
    )
