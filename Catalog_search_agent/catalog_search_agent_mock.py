import json
import re

PRODUCTS: list[dict] = json.load(open("products.json"))


def search_products(query, category=None, max_price=None, min_rating=None):
    results = list(PRODUCTS)
    query_lower = query.lower()
    results = [p for p in results if query_lower in p["name"].lower() or query_lower in p["description"].lower()]
    if category:
        results = [p for p in results if p["category"].lower() == category.lower()]
    if max_price is not None:
        results = [p for p in results if p["price"] <= max_price]
    if min_rating is not None:
        results = [p for p in results if p["rating"] >= min_rating]
    return results


def get_product_details(product_id):
    return next((p for p in PRODUCTS if p["id"] == product_id), None)


def list_categories():
    return sorted(set(p["category"] for p in PRODUCTS))


CATEGORY_KEYWORDS = {
    "electronics": "Electronics", "tech": "Electronics", "gadget": "Electronics",
    "home": "Home & Kitchen", "kitchen": "Home & Kitchen", "cook": "Home & Kitchen",
    "furniture": "Furniture", "chair": "Furniture", "desk": "Furniture",
    "grocery": "Groceries", "food": "Groceries", "tea": "Groceries", "drink": "Groceries",
    "sport": "Sports & Fitness", "fitness": "Sports & Fitness", "yoga": "Sports & Fitness", "run": "Sports & Fitness",
}


def extract_info(text):
    text_lower = text.lower()
    category = None
    for kw, cat in CATEGORY_KEYWORDS.items():
        if kw in text_lower:
            category = cat
            break
    prices = re.findall(r'\$?(\d+\.?\d*)', text_lower)
    max_price = None
    for p in prices:
        val = float(p)
        if "under" in text_lower or "below" in text_lower or "less" in text_lower or "budget" in text_lower:
            if max_price is None or val > max_price:
                max_price = val
        if "<" in text or "max" in text_lower:
            if max_price is None or val > max_price:
                max_price = val
    if text_lower.startswith("show me") or text_lower.startswith("find") or text_lower.startswith("search"):
        text_lower = re.sub(r'^(show me|find|search for|search|i want|i need|looking for|get me)\s*', '', text_lower)
        for kw in list(CATEGORY_KEYWORDS.keys()):
            text_lower = text_lower.replace(kw, "")
        for phrase in ["under", "below", "less than", "cheaper than", "max", "budget"]:
            text_lower = re.sub(rf'\b{phrase}\s*\d+\.?\d*', '', text_lower)
        text_lower = text_lower.replace("$", "").replace("  ", " ").strip()
        return text_lower, category, max_price
    return text, category, max_price


def handle_input(user_input):
    text = user_input.lower().strip()

    if text in ("exit", "quit"):
        return None

    m = re.search(r'product\s*(\d+)|#?\s*(\d+)', text)
    if m and ("detail" in text or "info" in text or "more" in text or "tell" in text or "about" in text or m.group(1)):
        pid = int(m.group(1) or m.group(2))
        p = get_product_details(pid)
        if not p:
            return f"No product found with ID {pid}."
        status = "In Stock" if p["stock"] > 0 else "OUT OF STOCK"
        return (
            f"[{p['id']}] {p['name']}\n"
            f"   Category: {p['category']}\n"
            f"   Price: ${p['price']:.2f}\n"
            f"   Rating: {p['rating']}/5\n"
            f"   Status: {status}\n"
            f"   {p['description']}"
        )

    if "categories" in text or "category" in text:
        cats = list_categories()
        return "Available categories:\n  " + "\n  ".join(cats)

    q, category, max_price = extract_info(user_input)
    if q == text and not category and not max_price:
        q = text
    if q == text:
        results = search_products(text)
    else:
        results = search_products(q, category=category, max_price=max_price)

    if not results:
        return f"No products found for '{text}'."
    out = [f"Found {len(results)} product(s):"]
    for p in results:
        status = "In Stock" if p["stock"] > 0 else "OUT OF STOCK"
        out.append(f"  [{p['id']}] {p['name']} — ${p['price']:.2f} | Rating: {p['rating']} | {status}")
        out.append(f"         {p['description']}")
    return "\n".join(out)


def main():
    print("=" * 60)
    print("  Catalog Search Agent (FREE - Mock/Offline Mode)")
    print("  Type 'exit' to quit")
    print("=" * 60)
    print("  Try: 'show me electronics under $150'")
    print("       'tell me about product 6'")
    print("       'what categories are there?'")
    print("=" * 60)
    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user_input:
            continue
        result = handle_input(user_input)
        if result is None:
            break
        print(f"\nAssistant:\n{result}")


if __name__ == "__main__":
    main()
