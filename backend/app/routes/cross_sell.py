from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.models import CrossSellResult
from app.services.cross_sell import get_cross_sell

router = APIRouter(prefix="/api/cross-sell", tags=["cross-sell"])


@router.get("/{product_id}", response_model=CrossSellResult)
async def cross_sell_endpoint(
    product_id: int,
    cart_ids: Optional[str] = Query(None, description="Comma-separated product IDs in cart"),
):
    cart_list = [int(x.strip()) for x in cart_ids.split(",") if x.strip()] if cart_ids else None
    return get_cross_sell(product_id, cart_list)


@router.post("/batch")
async def cross_sell_batch(body: dict):
    product_ids = body.get("product_ids", [])
    if not product_ids:
        raise HTTPException(400, "product_ids is required")
    cart_ids = body.get("cart_ids")
    results = {}
    for pid in product_ids:
        result = get_cross_sell(pid, cart_ids)
        if result.recommendations:
            results[str(pid)] = result.model_dump()
    return {"results": results}
