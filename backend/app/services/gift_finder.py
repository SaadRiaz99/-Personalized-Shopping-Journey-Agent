from typing import Optional
from shared.products import ALL_PRODUCTS, CATEGORIES
from app.models import GiftRecipient, GiftRecommendation, GiftFinderResult


def find_gifts(recipient: GiftRecipient) -> GiftFinderResult:
    results = list(ALL_PRODUCTS)
    match_reasons_map: dict[int, list[str]] = {}
    scores: dict[int, float] = {}

    for p in results:
        pid = p["id"]
        reasons = []
        score = 0.0

        if recipient.interests:
            interest_hits = sum(
                1 for interest in recipient.interests
                if interest.lower() in p["name"].lower()
                or interest.lower() in p["description"].lower()
                or interest.lower() in [t.lower() for t in p.get("tags", [])]
            )
            if interest_hits > 0:
                reasons.append(f"Matches interest{(chr(115) if interest_hits > 1 else '')}: {', '.join(recipient.interests)}")
                score += interest_hits * 25

        if recipient.occasion:
            occasion_lower = recipient.occasion.lower()
            occasion_keywords = {
                "birthday": ["birthday", "celebrate", "gift", "special"],
                "anniversary": ["anniversary", "romantic", "love", "couple"],
                "wedding": ["wedding", "bridal", "couple", "gift"],
                "christmas": ["christmas", "holiday", "festive", "winter"],
                "graduation": ["graduation", "success", "achievement", "congrats"],
                "valentine": ["valentine", "romantic", "love", "heart"],
                "mother's day": ["mother", "family", "love", "appreciation"],
                "father's day": ["father", "family", "appreciation", "gift"],
                "housewarming": ["home", "decor", "kitchen", "furniture"],
            }
            for occasion_name, keywords in occasion_keywords.items():
                if occasion_name in occasion_lower or occasion_lower in occasion_name:
                    kw_hits = sum(1 for kw in keywords if kw.lower() in p["name"].lower() or kw.lower() in p["description"].lower())
                    if kw_hits > 0:
                        reasons.append(f"Great for {recipient.occasion}")
                        score += kw_hits * 15
                        break

        if recipient.age_group:
            age_map = {
                "infant": (0, 20),
                "toddler": (0, 30),
                "child": (10, 50),
                "teen": (20, 100),
                "young adult": (25, 150),
                "adult": (30, 200),
                "senior": (20, 100),
            }
            for age_label, (age_min, age_max) in age_map.items():
                if age_label in recipient.age_group.lower() or recipient.age_group.lower() in age_label:
                    if age_min <= p["price"] <= age_max:
                        reasons.append(f"Age-appropriate for {recipient.age_group}")
                        score += 10
                    break

        if recipient.relationship:
            rel_map = {
                "spouse": ["romantic", "love", "jewelry", "accessories"],
                "parent": ["appreciation", "home", "comfort", "practical"],
                "sibling": ["fun", "entertainment", "games", "sports"],
                "friend": ["fun", "trendy", "gift", "accessories"],
                "child": ["fun", "educational", "games", "toys"],
                "partner": ["romantic", "love", "jewelry", "personalized"],
                "coworker": ["professional", "accessories", "desk", "practical"],
            }
            for rel, rel_keywords in rel_map.items():
                if rel in recipient.relationship.lower():
                    kw_hits = sum(1 for kw in rel_keywords if kw.lower() in p["name"].lower() or kw.lower() in p["description"].lower() or kw.lower() in [t.lower() for t in p.get("tags", [])])
                    if kw_hits > 0:
                        reasons.append(f"Thoughtful for {recipient.relationship}")
                        score += kw_hits * 10
                    break

        if recipient.gender_preference:
            gender_lower = recipient.gender_preference.lower()
            gender_tags = [t.lower() for t in p.get("tags", [])]
            if gender_lower == "male" and ("men" in p["category"].lower() or "men" in gender_tags or "male" in gender_tags):
                reasons.append("Matches gender preference")
                score += 10
            elif gender_lower == "female" and ("women" in p["category"].lower() or "women" in gender_tags or "female" in gender_tags):
                reasons.append("Matches gender preference")
                score += 10

        if recipient.budget:
            budget_upper = recipient.budget * 1.15
            budget_lower = recipient.budget * 0.15
            if budget_lower <= p["price"] <= budget_upper:
                if p["price"] <= recipient.budget:
                    reasons.append(f"Under ${recipient.budget:.0f} budget")
                    score += 20
                else:
                    score += 5

        score += p.get("rating", 0) * 2

        if reasons:
            match_reasons_map[pid] = reasons
            scores[pid] = score

    scored_products = [
        (p, scores[pid], match_reasons_map[pid])
        for p in results if pid in scores
    ]
    scored_products.sort(key=lambda x: x[1], reverse=True)

    occasion_noun = recipient.occasion if recipient.occasion else "gift"
    relationship_noun = f" for {recipient.relationship}" if recipient.relationship else ""
    summary_parts = []
    if scored_products:
        summary_parts.append(f"Found {len(scored_products)} {occasion_noun} ideas{relationship_noun}")
        top_price = scored_products[0][0]["price"]
        summary_parts.append(f"ranging from ${min(p[0]['price'] for p in scored_products):.0f} to ${max(p[0]['price'] for p in scored_products):.0f}")
    else:
        summary_parts.append(f"No gift ideas found{relationship_noun} for {recipient.occasion if recipient.occasion else 'this criteria'}. Try broadening your search.")
    summary = ". ".join(summary_parts)

    recommendations = [
        GiftRecommendation(product=p, relevance_score=round(score / 100, 2), match_reasons=reasons)
        for p, score, reasons in scored_products[:20]
    ]

    return GiftFinderResult(
        recipient=recipient,
        recommendations=recommendations,
        total_found=len(recommendations),
        summary=summary,
    )
