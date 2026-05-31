"""Catalog search using shared product data source."""

from shared.products import (
    ALL_PRODUCTS as CATALOG_PRODUCTS,
    CATEGORIES,
    search_products,
    get_product,
    list_categories,
    get_recommendations_by_category,
)


def search_simple(query: str) -> list[dict]:
    result = search_products(query=query)
    return result["products"]
