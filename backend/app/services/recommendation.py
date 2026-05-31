from app.models import Product, UserPreferences
from shared.products import search_products as catalog_search, get_product as catalog_get_product


def _to_product(d: dict) -> Product:
    return Product(
        id=str(d["id"]),
        name=d["name"],
        description=d.get("description", ""),
        price=d["price"],
        category=d["category"],
        rating=d.get("rating", 0.0),
        tags=[d["category"].lower()],
        sku=f"SKU-{d['id']:04d}",
    )


SAMPLE_PRODUCTS: list[Product] = [_to_product(p) for p in catalog_search(page_size=100)["products"]]


def get_recommendations(prefs: UserPreferences) -> list[Product]:
    result = catalog_search(
        category=prefs.categories[0] if prefs.categories else None,
        max_price=prefs.price_max,
        min_price=prefs.price_min,
        sort_by="rating",
        page_size=20,
    )
    filtered = [_to_product(p) for p in result["products"]]
    if prefs.brands:
        filtered = [p for p in filtered if any(b.lower() in p.name.lower() for b in prefs.brands)]
    return filtered


def search_products(query: str) -> list[Product]:
    result = catalog_search(query=query, page_size=20)
    return [_to_product(p) for p in result["products"]]
