from app.models import Product, UserPreferences

SAMPLE_PRODUCTS = [
    Product(id="p1", name="Wireless Headphones", description="Noise-cancelling Bluetooth headphones", price=249.99, category="Electronics", rating=4.5, tags=["audio", "wireless", "bluetooth"]),
    Product(id="p2", name="Running Shoes", description="Lightweight performance running shoes", price=129.99, category="Sports", rating=4.3, tags=["shoes", "running", "fitness"]),
    Product(id="p3", name="Coffee Maker", description="Programmable 12-cup drip coffee maker", price=79.99, category="Home", rating=4.1, tags=["kitchen", "coffee", "appliance"]),
    Product(id="p4", name="Smart Watch", description="Fitness tracker with heart rate monitor", price=199.99, category="Electronics", rating=4.6, tags=["wearable", "fitness", "smart"]),
    Product(id="p5", name="Leather Jacket", description="Genuine leather biker jacket", price=349.99, category="Fashion", rating=4.4, tags=["clothing", "leather", "jacket"]),
    Product(id="p6", name="Yoga Mat", description="Non-slip exercise yoga mat", price=39.99, category="Sports", rating=4.2, tags=["fitness", "yoga", "exercise"]),
    Product(id="p7", name="Bluetooth Speaker", description="Portable waterproof speaker", price=59.99, category="Electronics", rating=4.0, tags=["audio", "portable", "waterproof"]),
    Product(id="p8", name="Desk Lamp", description="LED desk lamp with adjustable brightness", price=49.99, category="Home", rating=4.3, tags=["lighting", "office", "led"]),
]


def get_recommendations(prefs: UserPreferences) -> list[Product]:
    filtered = [p for p in SAMPLE_PRODUCTS if prefs.price_min <= p.price <= prefs.price_max]
    if prefs.categories:
        filtered = [p for p in filtered if p.category in prefs.categories]
    if prefs.brands:
        filtered = [p for p in filtered if any(b.lower() in p.name.lower() for b in prefs.brands)]
    return sorted(filtered, key=lambda p: p.rating, reverse=True)


def search_products(query: str) -> list[Product]:
    q = query.lower()
    return [p for p in SAMPLE_PRODUCTS if q in p.name.lower() or q in p.description.lower() or q in p.category.lower() or any(q in t.lower() for t in p.tags)]
