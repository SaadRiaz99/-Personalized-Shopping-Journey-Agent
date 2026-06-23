from typing import Optional
from shared.products import ALL_PRODUCTS, CATEGORIES
from app.models import CrossSellItem, CrossSellResult


COMPLEMENTARY_MAP: dict[str, list[str]] = {
    "Electronics": ["Accessories", "Electronics"],
    "Fashion": ["Accessories", "Fashion"],
    "Home": ["Home", "Electronics"],
    "Sports": ["Sports", "Fashion", "Accessories"],
    "Accessories": ["Electronics", "Fashion"],
}

UPSELL_CATEGORY_MAP: dict[str, list[str]] = {
    "Electronics": ["Electronics"],
    "Fashion": ["Fashion"],
    "Home": ["Home"],
    "Sports": ["Sports"],
}


def _tag_overlap(a_tags: list[str], b_name: str, b_desc: str, b_tags: list[str]) -> int:
    combined_b = f"{b_name} {b_desc} {' '.join(b_tags)}".lower()
    return sum(1 for t in a_tags if t.lower() in combined_b)


def get_cross_sell(product_id: int, cart_product_ids: Optional[list[int]] = None) -> CrossSellResult:
    source = next((p for p in ALL_PRODUCTS if p["id"] == product_id), None)
    if not source:
        return CrossSellResult(source_product={"id": product_id}, recommendations=[])

    cart_ids = set(cart_product_ids or [])
    candidates = [p for p in ALL_PRODUCTS if p["id"] != product_id and p["id"] not in cart_ids]
    source_cat = source["category"]
    source_tags = source.get("tags", [])
    source_name_lower = source["name"].lower()

    recommendations: list[CrossSellItem] = []
    seen_ids: set[int] = set()

    comp_categories = COMPLEMENTARY_MAP.get(source_cat, [])
    upsell_categories = UPSELL_CATEGORY_MAP.get(source_cat, [])

    # Complementary picks: products in related categories that share tags/keywords
    for p in candidates:
        pid = p["id"]
        if pid in seen_ids:
            continue
        p_cat = p["category"]
        if p_cat in comp_categories:
            overlap = _tag_overlap(source_tags, p["name"], p["description"], p.get("tags", []))
            if overlap > 0 or p_cat != source_cat:
                score = overlap * 20 + p.get("rating", 0) * 5
                if p["price"] <= source["price"] * 1.5:
                    recommendations.append(CrossSellItem(
                        product=p,
                        type="complementary",
                        reason=f"Pairs well with {source['name']}" if overlap > 0 else f"Popular in {p_cat} category",
                        match_score=round(min(score / 100, 0.99), 2),
                    ))
                    seen_ids.add(pid)

    # Upsell picks: higher-priced items in same category
    for p in candidates:
        pid = p["id"]
        if pid in seen_ids:
            continue
        p_cat = p["category"]
        if p_cat in upsell_categories and p["price"] > source["price"] * 1.3:
            overlap = _tag_overlap(source_tags, p["name"], p["description"], p.get("tags", []))
            if overlap > 0 or p_cat == source_cat:
                rating_bonus = p.get("rating", 0) * 8
                price_ratio = min(p["price"] / source["price"], 5.0)
                score = overlap * 15 + rating_bonus + (price_ratio * 5)
                recommendations.append(CrossSellItem(
                    product=p,
                    type="upsell",
                    reason=f"Premium upgrade from {source['name']} — ${p['price']:.0f}",
                    match_score=round(min(score / 100, 0.99), 2),
                ))
                seen_ids.add(pid)

    # Accessory picks: lower-priced items in categories related to source
    for p in candidates:
        pid = p["id"]
        if pid in seen_ids:
            continue
        p_cat = p["category"]
        is_accessory_cat = p_cat in ["Accessories"] or (
            p_cat != source_cat and p_cat in comp_categories
        )
        if is_accessory_cat and p["price"] <= source["price"] * 0.6:
            overlap = _tag_overlap(source_tags, p["name"], p["description"], p.get("tags", []))
            if overlap > 0 or not source_tags:
                score = overlap * 25 + p.get("rating", 0) * 3
                recommendations.append(CrossSellItem(
                    product=p,
                    type="accessory",
                    reason=f"Essential accessory for {source['name']}",
                    match_score=round(min(score / 100, 0.99), 2),
                ))
                seen_ids.add(pid)

    recommendations.sort(key=lambda x: x.match_score, reverse=True)

    cart_context = []
    if cart_product_ids:
        cart_context = [p for p in ALL_PRODUCTS if p["id"] in cart_ids]

    return CrossSellResult(
        source_product=source,
        recommendations=recommendations[:12],
        cart_context=cart_context,
    )
