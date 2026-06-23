import os
import sys
import shutil
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parents[1]))

TEST_DIR = Path(__file__).parent / ".test_data"
TEST_DB_PATH = TEST_DIR / "rag_app.db"
TEST_CHROMA_DIR = TEST_DIR / "chromadb"

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"
os.environ["CHROMA_PERSIST_DIR"] = str(TEST_CHROMA_DIR)
os.environ["JWT_SECRET_KEY"] = "test-secret-key"

from app.database import init_db
from app.auth import seed_users
from app.services.vector_store import vector_store


def pytest_configure(config):
    if TEST_DIR.exists():
        shutil.rmtree(TEST_DIR)
    TEST_DIR.mkdir(parents=True, exist_ok=True)
    init_db()
    seed_users()


def pytest_unconfigure(config):
    from app.services.vector_store import VectorStore
    VectorStore._instance = None
    VectorStore._client = None
    import gc
    gc.collect()
    if TEST_DIR.exists():
        shutil.rmtree(TEST_DIR, ignore_errors=True)
