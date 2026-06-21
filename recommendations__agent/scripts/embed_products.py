import json
import os
import sys
import time
import uuid
import pathlib
from collections import defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    VectorParams, Distance, PointStruct, PayloadSchemaType,
)
from sentence_transformers import SentenceTransformer

# ── Config ──────────────────────────────────────────────────────────────
DATA_FILE   = pathlib.Path(__file__).parent.parent / "data" / "amazon_products_clean.json"
TARGET      = 50_000
CAP_PER_CAT = 500
DIM         = 384
MODEL_NAME  = "all-MiniLM-L6-v2"
COLLECTION  = "products"
BATCH_SIZE  = 500

QDRANT_URL     = os.getenv("QDRANT_URL", "")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")

REAL_PRODUCT_NOUNS = {
    "laptop", "phone", "tv", "television", "monitor", "keyboard",
    "mouse", "tablet", "headphone", "speaker", "camera", "printer",
    "shirt", "pants", "jeans", "jacket", "shoes", "dress", "hat",
    "socks", "watch", "sofa", "chair", "table", "bed", "lamp",
    "cookware", "pan", "pot", "knife", "book", "novel", "guide",
    "manual", "racket", "ball", "bike", "tent", "cream", "lotion",
    "shampoo", "soap", "perfume", "toy", "game", "doll", "car",
    "tire", "battery", "charger", "cable", "bag", "backpack",
    "wallet", "sunglasses", "gloves", "scarf", "bracelet",
    "necklace", "ring", "earring", "pillow", "blanket", "towel",
    "curtain", "rug", "vase", "clock", "mirror", "frame",
    "notebook", "pen", "pencil", "paper", "folder", "stapler",
    "drill", "hammer", "screwdriver", "paint", "brush", "filter",
    "sensor", "light", "fan", "heater", "vacuum", "cleaner",
    "blender", "toaster", "microwave", "fridge", "washer", "dryer",
    "grill", "earbud", "adapter", "hub", "router",
    "mousepad", "stand", "holder", "strap", "case",
    "cover", "protector", "screen", "oil", "supplement",
    "vitamin", "protein", "mask", "sanitizer", "towel",
    "sheet", "comforter", "pillowcase", "mat", "decor",
    "puzzle", "lego", "action", "figure", "card", "console",
    "controller", "headset", "mount", "bracket", "lock", "safe",
    "alarm", "bulb", "switch", "outlet", "plug", "thermostat",
    "hose", "nozzle", "blade", "bit", "saw", "level", "tape",
    "glue", "roller", "tray", "luggage", "suitcase", "duffel",
    "tote", "purse", "handbag", "belt", "cap", "beanie", "glove",
    "boot", "sandal", "slipper", "sneaker", "loafer", "heel",
    "hoodie", "sweater", "cardigan", "vest", "blazer", "tie",
    "short", "legging", "jogger", "sweatpant", "uniform", "costume",
    "lingerie", "pajama", "robe", "swimsuit", "bikini", "trunk",
    "bra", "underwear", "sock", "tights", "hose", "suspenders",
    "food", "snack", "drink", "coffee", "tea", "water", "soda",
    "juice", "protein", "bar", "shake", "powder",
}

# ── Helpers ─────────────────────────────────────────────────────────────
def has_product_noun(title):
    return any(noun in title.lower() for noun in REAL_PRODUCT_NOUNS)

def embed_text(text):
    return model.encode(text, normalize_embeddings=True).tolist()

def compute_discount_pct(price, list_price):
    if price and list_price and isinstance(price, (int, float)) and isinstance(list_price, (int, float)):
        if list_price > 0 and list_price > price:
            return round((1 - price / list_price) * 100, 1)
    return None

def extract_brand(title):
    stop_words = {"the", "a", "an", "for", "and", "with", "in", "of", "to", "is"}
    words = title.split()
    brand_parts = []
    for w in words:
        w_clean = w.strip("(),\"'.")
        if not w_clean or w_clean.lower() in stop_words:
            break
        if any(c.isdigit() for c in w_clean):
            break
        if len(w_clean) < 2:
            break
        brand_parts.append(w_clean)
    return " ".join(brand_parts) if brand_parts else ""

# ── Phase 1: Load & Filter ──────────────────────────────────────────────
phase = time.time()
print("Filtering products from 1.26M...")
sys.stdout.flush()

with open(DATA_FILE, "r", encoding="utf-8") as f:
    all_products = json.load(f)

print(f"  Loaded {len(all_products):,} products")
sys.stdout.flush()

required_fields = {"id", "title", "category_id", "price", "rating", "review_count", "image_url"}

qualified = []
removed_no_noun = 0
removed_other = 0

for p in all_products:
    title       = (p.get("title") or "").strip()
    price       = p.get("price")
    rating      = p.get("rating")
    review_cnt  = p.get("review_count")
    image_url   = (p.get("image_url") or "").strip()
    category_id = str(p.get("category_id") or "").strip()

    # Missing required fields
    if not all(k in p and p[k] is not None for k in required_fields):
        removed_other += 1
        continue

    # Title length
    if len(title) <= 10 or len(title) >= 200:
        removed_other += 1
        continue

    # Price
    if not isinstance(price, (int, float)) or price <= 0:
        removed_other += 1
        continue

    # Rating 4.0–5.0 only
    if not isinstance(rating, (int, float)) or rating < 4.0 or rating > 5.0:
        removed_other += 1
        continue

    # Review count
    if not isinstance(review_cnt, (int, float)) or review_cnt <= 10:
        removed_other += 1
        continue

    # Image URL
    if not image_url.startswith("https://"):
        removed_other += 1
        continue

    # Category
    if not category_id:
        removed_other += 1
        continue

    # Product noun check
    if not has_product_noun(title):
        removed_no_noun += 1
        continue

    qualified.append(p)

print(f"  Removed (missing/no noun/other): {removed_other:,}")
print(f"  Removed (no product noun):       {removed_no_noun:,}")
print(f"  Qualified products after filters: {len(qualified):,}")
print(f"  Phase 1 time: {time.time() - phase:.1f}s")
sys.stdout.flush()

# ── Phase 2: Rank & Sample ─────────────────────────────────────────────
phase = time.time()
print()
print("Ranking top rated products per category...")
sys.stdout.flush()

# Group by category
by_cat = defaultdict(list)
for p in qualified:
    by_cat[p["category_id"]].append(p)

# Sort within each category: rating DESC, review_count DESC
for cid in by_cat:
    by_cat[cid].sort(key=lambda x: (-x["rating"], -x["review_count"]))

# Take top CAP_PER_CAT from each category
selected = []
cat_counts = {}
for cid, items in sorted(by_cat.items()):
    taken = items[:CAP_PER_CAT]
    cat_counts[cid] = len(taken)
    selected.extend(taken)

print(f"  Categories with products: {len(by_cat)}")
print(f"  After per-category cap ({CAP_PER_CAT} max): {len(selected):,}")

# Fill remaining slots from globally highest rated
if len(selected) < TARGET:
    remaining_needed = TARGET - len(selected)
    already_ids = {p["id"] for p in selected}
    remaining_pool = [p for p in qualified if p["id"] not in already_ids]
    remaining_pool.sort(key=lambda x: (-x["rating"], -x["review_count"]))
    fill = remaining_pool[:remaining_needed]
    for p in fill:
        cat_counts[p["category_id"]] = cat_counts.get(p["category_id"], 0) + 1
    selected.extend(fill)
    print(f"  Filled remaining {len(fill)} from global pool")

# Trim if over
if len(selected) > TARGET:
    selected.sort(key=lambda x: (-x["rating"], -x["review_count"]))
    selected = selected[:TARGET]

print(f"  Selected {len(selected):,} best rated products")
sys.stdout.flush()

# Category stats
cat_ratings = defaultdict(list)
for p in selected:
    cat_ratings[p["category_id"]].append(p["rating"])
highest_cat = max(cat_ratings, key=lambda c: sum(cat_ratings[c]) / len(cat_ratings[c]))
lowest_cat  = min(cat_ratings, key=lambda c: sum(cat_ratings[c]) / len(cat_ratings[c]))
print(f"  Highest rated category: {highest_cat} (avg rating: {sum(cat_ratings[highest_cat])/len(cat_ratings[highest_cat]):.2f})")
print(f"  Lowest rated category:  {lowest_cat} (avg rating: {sum(cat_ratings[lowest_cat])/len(cat_ratings[lowest_cat]):.2f})")
print(f"  Phase 2 time: {time.time() - phase:.1f}s")
sys.stdout.flush()

# ── Phase 3: Embed & Upload ────────────────────────────────────────────
phase = time.time()
print()
print("Loading embedding model...")
model = SentenceTransformer(MODEL_NAME)
print(f"  Model loaded: {MODEL_NAME}")
sys.stdout.flush()

print("Connecting to Qdrant Cloud...")
client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=60)

# Delete & recreate
if client.collection_exists(COLLECTION):
    print(f"  Deleting existing '{COLLECTION}' collection...")
    client.delete_collection(COLLECTION)

print(f"  Creating '{COLLECTION}' collection (size={DIM}, distance=Cosine)...")
client.create_collection(
    collection_name=COLLECTION,
    vectors_config=VectorParams(size=DIM, distance=Distance.COSINE),
)

print("  Creating payload indexes...")
    for field, schema in [
        ("category_name",  PayloadSchemaType.KEYWORD),
    ("price",          PayloadSchemaType.FLOAT),
    ("rating",         PayloadSchemaType.FLOAT),
    ("review_count",   PayloadSchemaType.INTEGER),
    ("in_stock",       PayloadSchemaType.BOOL),
]:
    client.create_payload_index(
        collection_name=COLLECTION,
        field_name=field,
        field_schema=schema,
    )

print(f"  Uploading {len(selected)} products in batches of {BATCH_SIZE}...")
sys.stdout.flush()

total_batches = (len(selected) + BATCH_SIZE - 1) // BATCH_SIZE
points_batch = []

for i, p in enumerate(selected):
    title       = p.get("title", "")
    category_id = p.get("category_id", "")
    brand       = extract_brand(title)
    embedding_text = " ".join(v for v in [title, str(category_id), brand] if v)

    vector = embed_text(embedding_text)
    points_batch.append(PointStruct(
        id=uuid.uuid5(uuid.NAMESPACE_DNS, str(p["id"])),
        vector=vector,
        payload={
            "id":            str(p["id"]),
            "asin":          str(p["id"]),
            "title":         title,
            "category_id":   category_id,
            "category_name": category_id,
            "price":         p.get("price"),
            "original_price": p.get("list_price"),
            "discount_pct":  compute_discount_pct(p.get("price"), p.get("list_price")),
            "rating":        p.get("rating"),
            "review_count":  p.get("review_count"),
            "brand":         brand,
            "image_url":     p.get("image_url", ""),
            "in_stock":      True,
        },
    ))

    if len(points_batch) >= BATCH_SIZE or i == len(selected) - 1:
        batch_num = i // BATCH_SIZE + 1
        client.upsert(collection_name=COLLECTION, points=points_batch)
        points_batch.clear()
        if batch_num % 10 == 0 or batch_num == total_batches:
            print(f"  Embedding and uploading batch {batch_num}/{total_batches}...")
            sys.stdout.flush()

print(f"  Upload complete.")
print(f"  Phase 3 time: {time.time() - phase:.1f}s")
sys.stdout.flush()

# ── Phase 4: Verification ──────────────────────────────────────────────
phase = time.time()
print()
print("=" * 70)
print("VERIFICATION")
print("=" * 70)
sys.stdout.flush()

# Count
count_result = client.count(COLLECTION)
total_vecs = count_result.count
print(f"Total vectors in Qdrant: {total_vecs:,}")

# Sample all points to compute stats (scroll through)
all_ratings = []
scroll = client.scroll(COLLECTION, limit=10000, with_payload=True, with_vectors=False)
while scroll[0]:
    for point in scroll[0]:
        r = point.payload.get("rating")
        if r is not None:
            all_ratings.append(r)
    if scroll[1] is None:
        break
    scroll = client.scroll(COLLECTION, limit=10000, offset=scroll[1], with_payload=True, with_vectors=False)

min_rating = min(all_ratings) if all_ratings else 0
avg_rating = sum(all_ratings) / len(all_ratings) if all_ratings else 0
print(f"Minimum rating in collection: {min_rating}")
print(f"Average rating across all products: {avg_rating:.2f}")

# Confirm min rating >= 4.0
assert min_rating >= 4.0, f"FAIL: min rating {min_rating} is below 4.0!"
print(f"  -> Minimum rating check: PASS (>= 4.0)")
sys.stdout.flush()

# Run 5 test semantic searches
test_queries = [
    "wireless headphones for music",
    "comfortable running shoes",
    "laptop for video editing",
    "gift for someone who loves cooking",
    "something for outdoor camping",
]

print()
for q in test_queries:
    print(f"---")
    print(f"Query: \"{q}\"")
    qvec = embed_text(q)
    hits = client.query_points(
        collection_name=COLLECTION,
        query=qvec,
        limit=3,
        with_payload=True,
    ).points
    for rank, hit in enumerate(hits, 1):
        pl = hit.payload
        assert pl["rating"] >= 4.0, f"FAIL: result rating {pl['rating']} < 4.0"
        print(f"  #{rank} [{pl['rating']}★ / {pl['review_count']:,} reviews] "
              f"{pl['title'][:70]} | {pl['category_id']} | ${pl['price']}")
    sys.stdout.flush()

print()
print(f"All results have rating >= 4.0: PASS")
print(f"Phase 4 time: {time.time() - phase:.1f}s")
print()
print("=" * 70)
print(f"Done. Collection '{COLLECTION}' has {total_vecs:,} vectors (all 4.0+ rating).")
print("=" * 70)

# Category contribution summary
print()
print("Category contributions (top 20):")
for cid, cnt in sorted(cat_counts.items(), key=lambda x: -x[1])[:20]:
    print(f"  {cid}: {cnt} products")
print(f"  ... and {len(cat_counts) - 20} more categories")
