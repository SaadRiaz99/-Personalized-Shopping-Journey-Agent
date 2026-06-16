import asyncio
import difflib
import json
import os
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models
from agents import (
    Agent,
    GuardrailFunctionOutput,
    InputGuardrailTripwireTriggered,
    RunContextWrapper,
    Runner,
    TResponseInputItem,
    function_tool,
    input_guardrail,
    set_tracing_disabled,
)
from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel

set_tracing_disabled(disabled=True)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

ZEN_API_KEY = os.environ.get("ZEN_API_KEY", "")
ZEN_BASE_URL = "https://opencode.ai/zen/v1"
ZEN_MODEL = os.environ.get("LLM_MODEL", "big-pickle")

DATA_DIR = Path(__file__).parent

# ---------------------------------------------------------------------------
# Product catalog
# ---------------------------------------------------------------------------

PRODUCTS: list[dict] = json.load(open(DATA_DIR / "products.json"))
FEEDBACK_STORE: dict[str, list[dict]] = {}

# ---------------------------------------------------------------------------
# Embedding / Qdrant (initialized lazily)
# ---------------------------------------------------------------------------

_embedder = None
_qdrant: QdrantClient | None = None
_qdrant_ready = False
COLLECTION_NAME = "catalog_products"
EMBED_DIM = 384  # all-MiniLM-L6-v2


def _get_embedder():
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedder


def _embed_text(text: str) -> list[float]:
    return _get_embedder().encode(text).tolist()


def _product_text(p: dict) -> str:
    return f"{p['name']} {p['description']} {p['category']}"


def ensure_qdrant_indexed():
    global _qdrant, _qdrant_ready
    if _qdrant_ready:
        return
    _qdrant = QdrantClient(":memory:")
    _qdrant.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=qdrant_models.VectorParams(
            size=EMBED_DIM, distance=qdrant_models.Distance.COSINE
        ),
    )
    points = []
    for p in PRODUCTS:
        vec = _embed_text(_product_text(p))
        points.append(qdrant_models.PointStruct(id=p["id"], vector=vec, payload=p))
    _qdrant.upsert(collection_name=COLLECTION_NAME, points=points)
    _qdrant_ready = True


def vector_search(query: str, top_k: int = 50) -> list[dict]:
    if not _qdrant_ready:
        ensure_qdrant_indexed()
    vec = _embed_text(query)
    hits = _qdrant.search(
        collection_name=COLLECTION_NAME,
        query_vector=vec,
        limit=top_k,
    )
    return [h.payload for h in hits]


# ---------------------------------------------------------------------------
# Hybrid search — combine semantic + vector
# ---------------------------------------------------------------------------

def hybrid_search(
    query: str,
    category: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    min_rating: float | None = None,
    semantic_weight: float = 0.4,
) -> list[dict]:
    results = list(PRODUCTS)
    if category:
        results = [p for p in results if p["category"].lower() == category.lower()]
    if min_price is not None:
        results = [p for p in results if p["price"] >= min_price]
    if max_price is not None:
        results = [p for p in results if p["price"] <= max_price]
    if min_rating is not None:
        results = [p for p in results if p["rating"] >= min_rating]

    semantic_scores = {p["id"]: _semantic_score(query, p) for p in results}
    max_ss = max(semantic_scores.values()) if semantic_scores else 1

    try:
        vector_results = vector_search(query, top_k=50)
        vector_ids = {p["id"] for p in vector_results}
        vector_rank = {pid: i for i, pid in enumerate(vector_ids)}
        max_vr = len(vector_ids)
    except Exception:
        vector_ids = set()
        vector_rank = {}
        max_vr = 1

    scored = []
    for p in results:
        ss = semantic_scores[p["id"]] / max_ss if max_ss else 0
        if p["id"] in vector_rank:
            vs = 1.0 - (vector_rank[p["id"]] / max_vr)
        else:
            vs = 0.0
        combined = semantic_weight * ss + (1 - semantic_weight) * vs
        if combined > 0:
            scored.append((p, combined))

    scored.sort(key=lambda x: -x[1])
    return [p for p, _ in scored]


# ---------------------------------------------------------------------------
# Provider setup — Zen (OpenCode)
# ---------------------------------------------------------------------------

_zen_client: AsyncOpenAI | None = None
_zen_model: OpenAIChatCompletionsModel | None = None
_provider_label: str | None = None


def build_model():
    global _zen_client, _zen_model, _provider_label
    if not ZEN_API_KEY:
        return None, None
    _zen_client = AsyncOpenAI(api_key=ZEN_API_KEY, base_url=ZEN_BASE_URL)
    _zen_model = OpenAIChatCompletionsModel(model=ZEN_MODEL, openai_client=_zen_client)
    _provider_label = f"OpenCode Zen ({ZEN_MODEL})"
    return _zen_model, _provider_label


# ---------------------------------------------------------------------------
# Context
# ---------------------------------------------------------------------------

@dataclass
class UserContext:
    user_id: str
    name: str
    preferred_categories: Optional[list[str]] = None
    max_budget: Optional[float] = None


# ---------------------------------------------------------------------------
# Structured output types
# ---------------------------------------------------------------------------

class ProductResult(BaseModel):
    id: int = Field(description="Product ID")
    name: str = Field(description="Product name")
    category: str = Field(description="Product category")
    price: float = Field(description="Current price in USD")
    rating: float = Field(description="Average customer rating (1-5)")
    in_stock: bool = Field(description="Whether the product is currently in stock")
    description: str = Field(description="Short product description")


class SearchResults(BaseModel):
    query: str = Field(description="The original search query")
    total_found: int = Field(description="Number of matching products")
    products: list[ProductResult] = Field(description="List of matching products")
    note: Optional[str] = Field(default=None, description="Any helpful note for the user")


class CategoriesResult(BaseModel):
    categories: list[str] = Field(description="Available product categories")
    total: int = Field(description="Number of categories")


class CatalogQueryCheck(BaseModel):
    is_catalog_query: bool = Field(description="Whether the user's query is about the product catalog")
    reasoning: str = Field(description="Reasoning for the classification")


# ---------------------------------------------------------------------------
# Semantic search helpers
# ---------------------------------------------------------------------------


def _tokenize(text: str) -> list[str]:
    text = text.lower()
    table = str.maketrans("-_/.,:;!?()[]{}\"'", " " * 17)
    text = text.translate(table)
    return [t for t in text.split() if len(t) > 1]


def _stem(word: str) -> str:
    w = word
    if len(w) > 4 and w.endswith("ing"):
        w = w[:-3]
    elif len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
        w = w[:-1]
    elif len(w) > 4 and w.endswith("ed"):
        w = w[:-2]
    return w


def _token_similarity(a: str, b: str) -> float:
    if a == b:
        return 1.0
    if _stem(a) == _stem(b):
        return 0.9
    shorter, longer = (a, b) if len(a) <= len(b) else (b, a)
    if len(shorter) >= len(longer) * 0.5 and shorter in longer:
        return 0.8
    return difflib.SequenceMatcher(None, a, b).ratio()


def _semantic_score(query: str, product: dict) -> float:
    q_tokens = _tokenize(query)
    if not q_tokens:
        return 1.0

    stops = {
        "the", "a", "an", "is", "are", "was", "were", "be", "to", "of", "in",
        "for", "on", "with", "at", "by", "from", "and", "or", "but", "not",
        "this", "that", "these", "those", "it", "its", "i", "you", "we", "they",
        "me", "my", "your", "our", "do", "does", "did", "have", "has", "had",
        "can", "will", "would", "could", "should", "may", "all", "each", "every",
        "some", "any", "no", "both", "what", "which", "who", "how", "why",
        "when", "where", "there", "here", "about", "up", "out", "if", "so",
    }
    relevant = [t for t in q_tokens if t not in stops]
    if not relevant:
        return 1.0

    name_tokens = _tokenize(product["name"])
    desc_tokens = _tokenize(product["description"])

    score = 0.0
    matched_strong = 0
    any_strong = False

    for qt in relevant:
        best = 0.0
        for pt in name_tokens:
            s = _token_similarity(qt, pt)
            if s > best:
                best = s
        for pt in desc_tokens:
            s = _token_similarity(qt, pt) * 0.7
            if s > best:
                best = s

        if best >= 0.7:
            matched_strong += 1
            any_strong = True
        score += best

    if not any_strong:
        return 0.0

    coverage = matched_strong / len(relevant)
    score *= (1 + coverage * 0.5)
    return score


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@function_tool
def search_products(
    ctx: RunContextWrapper[UserContext],
    query: str,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
) -> SearchResults:
    """Search the product catalog using hybrid semantic + vector search. Returns results sorted by relevance."""
    results = hybrid_search(query, category, min_price, max_price, min_rating)
    products = [
        ProductResult(
            id=p["id"], name=p["name"], category=p["category"],
            price=p["price"], rating=p["rating"],
            in_stock=p["stock"] > 0, description=p["description"],
        ) for p in results
    ]
    return SearchResults(query=query, total_found=len(products), products=products)


@function_tool
def get_product_details(product_id: int) -> ProductResult:
    """Get full details for a single product by its ID."""
    p = next((p for p in PRODUCTS if p["id"] == product_id), None)
    if not p:
        return ProductResult(id=product_id, name="Not found", category="", price=0, rating=0, in_stock=False, description=f"No product found with ID {product_id}.")
    return ProductResult(id=p["id"], name=p["name"], category=p["category"], price=p["price"], rating=p["rating"], in_stock=p["stock"] > 0, description=p["description"])


@function_tool
def list_categories(dummy: Optional[str] = None) -> str:
    """List all available product categories in the catalog."""
    cats = sorted(set(p["category"] for p in PRODUCTS))
    return f"Available categories ({len(cats)}): " + ", ".join(cats)


@function_tool
def add_feedback(
    ctx: RunContextWrapper[UserContext],
    product_id: int,
    rating: int,
    comment: Optional[str] = None,
) -> str:
    """Record user feedback (rating 1-5) for a product. Use this whenever a user rates or reviews a product."""
    uid = ctx.context.user_id
    if uid not in FEEDBACK_STORE:
        FEEDBACK_STORE[uid] = []
    entry = {"product_id": product_id, "rating": rating, "comment": comment}
    FEEDBACK_STORE[uid].append(entry)
    return f"Thanks! Your {rating}/5 rating for product {product_id} has been saved."


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------


def dynamic_instructions(ctx: RunContextWrapper[UserContext], agent: Agent[UserContext]) -> str:
    base = (
        "You are a friendly catalog search assistant. "
        "Help users find products by searching, browsing categories, and getting details.\n\n"
        "Guidelines:\n"
        "- Use search_products when filtering by name, category, price, or rating\n"
        "- Use get_product_details for more info on a specific product\n"
        "- Use list_categories to show available categories\n"
        "- Use add_feedback when a user rates or reviews a product (1-5 stars)\n"
        "- If a product is out of stock, mention it and suggest alternatives\n"
        "- Be concise but helpful"
    )
    user = ctx.context
    prefs = []
    if user.preferred_categories:
        prefs.append(f"Preferred categories: {', '.join(user.preferred_categories)}")
    if user.max_budget is not None:
        prefs.append(f"Max budget: ${user.max_budget:.2f}")
    if prefs:
        base += "\n\nUser preferences:\n" + "\n".join(prefs)
    return base


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

_agent_instance: Agent[UserContext] | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _agent_instance
    model, label = build_model()
    if model:
        guardrail_agent = Agent[UserContext](
            name="CatalogGuardrail",
            instructions=(
                "Determine if the user's query is about the product catalog. "
                "You must NOT use any tools. Only return a JSON object with "
                "'is_catalog_query' (bool) and 'reasoning' (str). "
                "Reject math, coding, general knowledge, or unrelated chat."
            ),
            output_type=CatalogQueryCheck,
            model=model,
        )

        @input_guardrail
        async def catalog_relevance_guardrail(
            ctx: RunContextWrapper[UserContext], agent: Agent[UserContext], input: str | list[TResponseInputItem]
        ) -> GuardrailFunctionOutput:
            try:
                result = await Runner.run(guardrail_agent, input, context=ctx.context)
                return GuardrailFunctionOutput(
                    output_info=result.final_output,
                    tripwire_triggered=not result.final_output.is_catalog_query,
                )
            except Exception:
                return GuardrailFunctionOutput(
                    output_info=CatalogQueryCheck(is_catalog_query=True, reasoning="Guardrail error, allowing query by default"),
                    tripwire_triggered=False,
                )

        _agent_instance = Agent[UserContext](
            name="CatalogSearchAgent",
            instructions=dynamic_instructions,
            model=model,
            tools=[search_products, get_product_details, list_categories, add_feedback],
            input_guardrails=[catalog_relevance_guardrail],
        )
        print(f"  Provider: {label}")
    else:
        print("  No ZEN_API_KEY set — agent queries will return 503")
    print("  Qdrant vector search ready")
    yield


app = FastAPI(title="Catalog Search Agent", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# REST endpoints
# ---------------------------------------------------------------------------


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "provider": _provider_label or "none",
        "products": len(PRODUCTS),
        "qdrant": _qdrant_ready,
        "zen_key_set": bool(ZEN_API_KEY),
    }


@app.get("/api/products/search")
async def api_search(
    query: str = "",
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    results = hybrid_search(query, category, min_price, max_price, min_rating)
    total = len(results)
    start = (page - 1) * page_size
    items = results[start: start + page_size]
    return {
        "query": query,
        "total_found": total,
        "page": page,
        "page_size": page_size,
        "products": [
            {
                "id": p["id"], "name": p["name"], "category": p["category"],
                "price": p["price"], "rating": p["rating"],
                "in_stock": p["stock"] > 0, "description": p["description"],
            }
            for p in items
        ],
    }


@app.get("/api/products/{product_id}")
async def api_product(product_id: int):
    p = next((p for p in PRODUCTS if p["id"] == product_id), None)
    if not p:
        raise HTTPException(404, f"Product {product_id} not found")
    return {
        "id": p["id"], "name": p["name"], "category": p["category"],
        "price": p["price"], "rating": p["rating"],
        "in_stock": p["stock"] > 0, "description": p["description"],
    }


@app.get("/api/categories")
async def api_categories():
    cats = sorted(set(p["category"] for p in PRODUCTS))
    return {"categories": cats, "total": len(cats)}


@app.post("/api/feedback")
async def api_feedback(product_id: int, rating: int, comment: str | None = None, user_id: str = "anonymous"):
    if rating < 1 or rating > 5:
        raise HTTPException(422, "Rating must be between 1 and 5")
    if user_id not in FEEDBACK_STORE:
        FEEDBACK_STORE[user_id] = []
    entry = {"product_id": product_id, "rating": rating, "comment": comment}
    FEEDBACK_STORE[user_id].append(entry)
    return {"status": "ok", "message": f"Thanks! Your {rating}/5 rating for product {product_id} has been saved."}


@app.post("/api/agent/query")
async def agent_query(
    query: str,
    user_id: str = "anonymous",
    name: str = "User",
    preferred_categories: str | None = None,
    max_budget: float | None = None,
):
    if not _agent_instance:
        raise HTTPException(503, "Agent not available — set ZEN_API_KEY")

    cats = preferred_categories.split(",") if preferred_categories else None
    ctx = UserContext(user_id=user_id, name=name, preferred_categories=cats, max_budget=max_budget)

    try:
        result = await Runner.run(_agent_instance, query, context=ctx)
        return {"response": str(result.final_output)}
    except InputGuardrailTripwireTriggered:
        return {
            "response": "I can only answer questions about the product catalog. Please ask me about products, categories, pricing, or availability."
        }


# ---------------------------------------------------------------------------
# Main entry
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("catalog_search_agent:app", host="0.0.0.0", port=8000, reload=True)
