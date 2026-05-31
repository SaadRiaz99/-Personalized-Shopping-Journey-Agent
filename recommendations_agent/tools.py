import json
import sys
from pathlib import Path
from typing import Optional

from agents import function_tool

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from shared.products import (
    ALL_PRODUCTS,
    search_products as shared_search,
    get_product,
    get_recommendations_by_category,
)


@function_tool
def search_products(
    query: str = "",
    category: Optional[str] = None,
    max_price: Optional[float] = None,
    min_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    sort_by: str = "relevance",
    page: int = 1,
    page_size: int = 20,
) -> str:
    """Search the product catalog by name, category, price range, rating, etc. Returns matching products."""
    result = shared_search(
        query=query,
        category=category,
        max_price=max_price,
        min_price=min_price,
        min_rating=min_rating,
        sort_by=sort_by,
        page=page,
        page_size=page_size,
    )
    return json.dumps(result)


@function_tool
def get_recommendations(category: str, limit: int = 10) -> str:
    """Get top-rated product recommendations for a given category."""
    products = get_recommendations_by_category(category, limit=limit)
    return json.dumps({"category": category, "count": len(products), "products": products})


@function_tool
def get_product_details(product_id: int) -> str:
    """Get full details for a single product by its numeric ID."""
    product = get_product(product_id)
    if product is None:
        return json.dumps({"error": f"No product found with ID {product_id}"})
    return json.dumps(product)


@function_tool
def compare_prices(product_ids: list[int]) -> str:
    """Compare prices across multiple products by their IDs. Returns a price comparison."""
    products = []
    for pid in product_ids:
        p = get_product(pid)
        if p:
            products.append({"id": p["id"], "name": p["name"], "price": p["price"], "rating": p["rating"], "category": p["category"]})
    products.sort(key=lambda x: x["price"])
    return json.dumps({"count": len(products), "products": products, "cheapest": products[0] if products else None, "most_expensive": products[-1] if products else None})
