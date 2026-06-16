import os
from typing import Optional

from fastapi import APIRouter, Body, HTTPException, Query
from openai import AsyncOpenAI

from app.services.catalog_search import search_products, get_product, list_categories
from app.services.agent_orchestrator import orchestrator


router = APIRouter(prefix="/api/catalog", tags=["catalog"])

ZEN_API_KEY = os.environ.get("ZEN_API_KEY", "")
ZEN_BASE_URL = "https://opencode.ai/zen/v1"
ZEN_MODEL = os.environ.get("LLM_MODEL", "big-pickle")


@router.get("/search")
async def catalog_search(
    query: str = "",
    category: Optional[str] = None,
    max_price: Optional[float] = None,
    min_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    sort_by: str = "relevance",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    return search_products(
        query=query,
        category=category,
        max_price=max_price,
        min_price=min_price,
        min_rating=min_rating,
        sort_by=sort_by,
        page=page,
        page_size=page_size,
    )


@router.get("/products/{product_id}")
async def catalog_product(product_id: int):
    product = get_product(product_id)
    if not product:
        raise HTTPException(404, f"Product {product_id} not found")
    return product


@router.get("/categories")
async def catalog_categories():
    return {"categories": list_categories(), "total": len(list_categories())}


@router.get("/agent/{agent_id}/search")
async def catalog_agent_search(agent_id: str):
    agent = orchestrator.get_agent(agent_id)
    if not agent:
        raise HTTPException(404, "Agent not found")
    result = await orchestrator.run_catalog_search(agent_id)
    return result


@router.post("/agent/query")
async def agent_query(
    query: str = Body(..., description="Natural language query"),
    user_id: str = Body("anonymous", description="User identifier"),
):
    if not ZEN_API_KEY:
        raise HTTPException(503, "Agent not available — set ZEN_API_KEY")
    if not query.strip():
        return {"response": "Please ask me a question about products in the catalog."}
    client = AsyncOpenAI(api_key=ZEN_API_KEY, base_url=ZEN_BASE_URL)
    response = await client.chat.completions.create(
        model=ZEN_MODEL,
        messages=[
            {"role": "system", "content": (
                "You are a friendly catalog search assistant with access to 906 products. "
                "Help users find products by name, category, price range, or rating. "
                "Be concise and helpful. If a product is out of stock, mention it."
            )},
            {"role": "user", "content": query},
        ],
    )
    return {"response": response.choices[0].message.content}
