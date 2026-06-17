import json
from typing import Optional

import httpx

from app.config import settings


async def generate_embeddings(texts: list[str], model: Optional[str] = None) -> list[list[float]]:
    if not texts:
        return []

    if not settings.llm_api_key:
        return _generate_fake_embeddings(texts)

    model = model or settings.embedding_model

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{settings.llm_endpoint}/embeddings",
            headers={
                "Authorization": f"Bearer {settings.llm_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "input": texts,
                "model": model,
            },
        )
        response.raise_for_status()
        data = response.json()
        return [item["embedding"] for item in data["data"]]


def _generate_fake_embeddings(texts: list[str]) -> list[list[float]]:
    import hashlib
    embeddings = []
    for text in texts:
        h = hashlib.md5(text.encode())
        seed = int(h.hexdigest()[:8], 16)
        rng = __import__("random").Random(seed)
        emb = [rng.random() * 2 - 1 for _ in range(128)]
        magnitude = sum(x * x for x in emb) ** 0.5
        emb = [x / magnitude for x in emb]
        embeddings.append(emb)
    return embeddings
