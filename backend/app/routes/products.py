from fastapi import APIRouter, Query
from app.models import Product
from app.services.recommendation import get_recommendations, search_products, SAMPLE_PRODUCTS

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("", response_model=list[Product])
async def list_products(
    category: str = Query(None),
    min_price: float = Query(0.0),
    max_price: float = Query(10000.0),
    search: str = Query(None),
):
    if search:
        return search_products(search)
    filtered = SAMPLE_PRODUCTS
    if category:
        filtered = [p for p in filtered if p.category == category]
    filtered = [p for p in filtered if min_price <= p.price <= max_price]
    return filtered
