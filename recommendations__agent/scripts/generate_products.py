import json
import random
import time
from pathlib import Path

from faker import Faker

fake = Faker()

TAG_POOL = [
    "sci-fi", "epic", "survival", "self-help", "productivity", "focus",
    "thriller", "action", "drama", "headphones", "audio", "laptop",
    "e-reader", "books", "furniture", "office", "smart-home", "lighting",
    "fantasy", "romance", "mystery", "horror", "comedy", "documentary",
    "wireless", "noise-canceling", "gaming", "portable", "4k", "smartphone",
    "tablet", "camera", "fitness", "wearable", "organic", "vegan",
    "sustainable", "handmade", "vintage", "minimalist", "ergonomic",
    "outdoor", "camping", "kitchen", "cooking", "pet", "toy", "educational",
    "board-game", "musical", "art", "craft", "gardening", "automotive",
    "health", "beauty", "fashion", "accessory", "sport", "travel",
]

CATEGORIES = ["Book", "Movie", "Electronics", "Home", "Apparel", "Health", "Toys"]

NUM_PRODUCTS = 1_000_000
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "products.json"


def generate_product(i: int) -> dict:
    num_tags = random.randint(1, 3)
    tags = random.sample(TAG_POOL, num_tags)
    return {
        "id": i + 13,
        "title": f"{fake.color_name()} {fake.catch_phrase()}",
        "category": CATEGORIES[i % len(CATEGORIES)],
        "tags": tags,
        "rating": round(random.uniform(1.0, 5.0), 1),
    }


def main():
    print(f"Generating {NUM_PRODUCTS:,} products...")
    start = time.perf_counter()

    products = [generate_product(i) for i in range(NUM_PRODUCTS)]

    elapsed = time.perf_counter() - start
    print(f"Generated {len(products):,} products in {elapsed:.1f}s")

    print(f"Writing to {OUTPUT_PATH}...")
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(products, f)

    file_size_mb = OUTPUT_PATH.stat().st_size / 1024 / 1024
    print(f"Written {file_size_mb:.1f} MB to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
