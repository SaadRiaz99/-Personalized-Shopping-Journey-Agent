import json
import os
import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    VectorParams, Distance, Batch, PointStruct,
    PayloadSchemaType,
)
from sentence_transformers import SentenceTransformer

DATA_FILE  = pathlib.Path(__file__).parent.parent / "data" / "products.json"
SAMPLE     = 50_000
DIM        = 384
MODEL_NAME = "all-MiniLM-L6-v2"
COLLECTION = "products"
BATCH_SIZE = 500

QDRANT_URL     = os.getenv("QDRANT_URL", "")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")

if not QDRANT_URL:
    print("ERROR: QDRANT_URL not set. Set it in .env")
    sys.exit(1)

def embed_text(text: str) -> list[float]:
    return model.encode(text, normalize_embeddings=True).tolist()

print("Loading embedding model...")
model = SentenceTransformer(MODEL_NAME)

print(f"Loading products from {DATA_FILE}...")
with open(DATA_FILE, "r", encoding="utf-8") as f:
    all_products = json.load(f)

if len(all_products) > SAMPLE:
    import random
    random.seed(42)
    products = random.sample(all_products, SAMPLE)
else:
    products = all_products

print(f"Products to embed: {len(products)}")

print("Connecting to Qdrant Cloud...")
client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
    timeout=60,
)

existing = client.collection_exists(COLLECTION)
if existing:
    info = client.get_collection(COLLECTION)
    count = client.count(COLLECTION).count
    print(f"Collection '{COLLECTION}' exists with {count} points")
    if count == 0:
        print("Collection is empty (likely auto-deleted). Recreating...")
        client.delete_collection(COLLECTION)
        existing = False
    else:
        print("Collection already has data. Skipping embedding.")
        sys.exit(0)

if not existing:
    print(f"Creating collection '{COLLECTION}'...")
    client.create_collection(
        collection_name=COLLECTION,
        vectors_config=VectorParams(size=DIM, distance=Distance.COSINE),
    )
    print("Creating payload indexes...")
    for field in ("category", "price", "rating", "in_stock"):
        client.create_payload_index(
            collection_name=COLLECTION,
            field_name=field,
            field_schema=PayloadSchemaType.KEYWORD if field == "category"
                          else PayloadSchemaType.FLOAT if field in ("price", "rating")
                          else PayloadSchemaType.BOOL,
        )

    points = []
    for i, p in enumerate(products):
        embedding_text = " ".join(
            str(v) for v in [
                p.get("title", ""),
                p.get("category", ""),
                " ".join(p.get("tags", [])),
            ] if v
        )
        vector = embed_text(embedding_text)
        points.append(PointStruct(
            id=p["id"],
            vector=vector,
            payload={
                "id":           p["id"],
                "title":        p.get("title", ""),
                "category":     p.get("category", ""),
                "price":        p.get("price"),
                "rating":       p.get("rating"),
                "in_stock":     p.get("in_stock"),
                "discount_pct": p.get("discount") or p.get("discount_pct"),
            },
        ))

        if len(points) >= BATCH_SIZE or i == len(products) - 1:
            client.upsert(collection_name=COLLECTION, points=points)
            points.clear()

        if (i + 1) % 1000 == 0:
            print(f"  Embedded {i + 1}/{len(products)} products")

    if points:
        client.upsert(collection_name=COLLECTION, points=points)

    final = client.count(COLLECTION).count
    print(f"Done. Collection '{COLLECTION}' has {final} vectors.")
