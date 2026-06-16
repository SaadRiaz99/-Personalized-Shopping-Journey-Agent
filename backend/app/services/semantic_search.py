"""Semantic search — pure Python, no external ML dependencies."""

import difflib
from typing import Optional

from shared.products import ALL_PRODUCTS


def _tokenize(text: str) -> list[str]:
    text = text.lower()
    table = str.maketrans("-_/.,:;!?()[]{}\"'", " " * 17)
    text = text.translate(table)
    return [t for t in text.split() if len(t) > 1]


def _stem(word: str) -> str:
    w = word
    if len(w) > 4 and w.endswith("ing"):
        w = w[:-3]
    elif len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
        w = w[:-1]
    elif len(w) > 4 and w.endswith("ed"):
        w = w[:-2]
    return w


def _token_similarity(a: str, b: str) -> float:
    if a == b:
        return 1.0
    if _stem(a) == _stem(b):
        return 0.9
    return difflib.SequenceMatcher(None, a, b).ratio()


def _semantic_score(query: str, product: dict) -> float:
    q_tokens = _tokenize(query)
    if not q_tokens:
        return 1.0
    stops = {
        "the", "a", "an", "is", "are", "was", "were", "be", "to", "of", "in",
        "for", "on", "with", "at", "by", "from", "and", "or", "but", "not",
        "this", "that", "these", "those", "it", "its", "i", "you", "we", "they",
        "me", "my", "your", "our", "do", "does", "did", "have", "has", "had",
        "can", "will", "would", "could", "should", "may", "all", "each", "every",
        "some", "any", "no", "both", "what", "which", "who", "how", "why",
        "when", "where", "there", "here", "about", "up", "out", "if", "so",
    }
    relevant = [t for t in q_tokens if t not in stops]
    if not relevant:
        return 1.0
    name_tokens = _tokenize(product["name"])
    desc_tokens = _tokenize(product["description"])
    score = 0.0
    matched_strong = 0
    any_strong = False
    for qt in relevant:
        best = 0.0
        for pt in name_tokens:
            s = _token_similarity(qt, pt)
            if s > best:
                best = s
        for pt in desc_tokens:
            s = _token_similarity(qt, pt) * 0.7
            if s > best:
                best = s
        if best >= 0.7:
            matched_strong += 1
            any_strong = True
        score += best
    if not any_strong:
        return 0.0
    coverage = matched_strong / len(relevant)
    score *= (1 + coverage * 0.5)
    return score


def search(
    query: str,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
) -> list[dict]:
    results = list(ALL_PRODUCTS)
    if category:
        results = [p for p in results if p["category"].lower() == category.lower()]
    if min_price is not None:
        results = [p for p in results if p["price"] >= min_price]
    if max_price is not None:
        results = [p for p in results if p["price"] <= max_price]
    if min_rating is not None:
        results = [p for p in results if p["rating"] >= min_rating]

    scored = [(p, _semantic_score(query, p)) for p in results]
    scored.sort(key=lambda x: -x[1])
    return [p for p, s in scored if s > 0]
