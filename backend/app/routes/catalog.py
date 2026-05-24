from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.services.catalog_search import search_products, get_product, list_categories
from app.services.agent_orchestrator import orchestrator

router = APIRouter(prefix="/api/catalog", tags=["catalog"])


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
