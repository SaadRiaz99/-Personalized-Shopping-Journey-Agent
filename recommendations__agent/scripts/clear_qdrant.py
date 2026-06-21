import os
import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from qdrant_client import QdrantClient

QDRANT_URL     = os.getenv("QDRANT_URL", "")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")

COLLECTION = "products"

if not QDRANT_URL:
    print("ERROR: QDRANT_URL not set. Set it in .env")
    sys.exit(1)

print("Connecting to Qdrant Cloud...")
client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=10)

if not client.collection_exists(COLLECTION):
    print(f"Collection '{COLLECTION}' does not exist. Nothing to delete.")
    sys.exit(0)

print(f"Found collection: {COLLECTION}")
print(f"Deleting collection: {COLLECTION}...")
client.delete_collection(COLLECTION)
print("Collection deleted successfully")

remaining = client.get_collections().collections
print(f"Remaining collections: {len(remaining)}")
for col in remaining:
    print(f"  - {col.name}")
