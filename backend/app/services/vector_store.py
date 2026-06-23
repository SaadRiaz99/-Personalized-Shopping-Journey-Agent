from pathlib import Path
from typing import Optional

import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.errors import NotFoundError


class VectorStore:
    _instance: Optional["VectorStore"] = None
    _client: Optional[chromadb.ClientAPI] = None

    DEFAULT_COLLECTION = "documents"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _get_client(self) -> chromadb.ClientAPI:
        if self._client is None:
            persist_dir = Path(settings.chroma_persist_dir)
            persist_dir.mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(
                path=str(persist_dir),
                settings=ChromaSettings(anonymized_telemetry=False),
            )
        return self._client

    def health_check(self) -> dict:
        try:
            client = self._get_client()
            heartbeat = client.heartbeat()
            return {
                "status": "healthy",
                "heartbeat": heartbeat,
                "persist_dir": settings.chroma_persist_dir,
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    def list_collections(self) -> list[dict]:
        try:
            client = self._get_client()
            collections = client.list_collections()
            result = []
            for c in collections:
                try:
                    result.append({"name": c.name, "count": c.count()})
                except Exception:
                    result.append({"name": c.name, "count": 0})
            return result
        except Exception:
            return []

    def get_or_create_collection(self, name: str = DEFAULT_COLLECTION):
        client = self._get_client()
        try:
            return client.get_collection(name)
        except (ValueError, NotFoundError):
            return client.create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"},
            )

    def add_chunks(self, chunks: list[dict], embeddings: list[list[float]], collection_name: str = DEFAULT_COLLECTION):
        if not chunks or not embeddings:
            return
        try:
            collection = self.get_or_create_collection(collection_name)
            ids = [c["id"] for c in chunks]
            documents = [c["content"] for c in chunks]
            metadatas = [c.get("metadata", {}) for c in chunks]
            collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
            )
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Failed to add chunks to vector store: {e}")

    def search(self, query_embedding: list[float], n_results: int = 5, collection_name: str = DEFAULT_COLLECTION) -> dict:
        try:
            collection = self.get_or_create_collection(collection_name)
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
            )
            return results
        except Exception as e:
            return {"ids": [[]], "distances": [[]], "documents": [[]], "metadatas": [[]], "error": str(e)}

    def search_with_filter(self, query_embedding: list[float], where: dict, n_results: int = 5, collection_name: str = DEFAULT_COLLECTION) -> dict:
        try:
            collection = self.get_or_create_collection(collection_name)
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where,
            )
            return results
        except Exception as e:
            return {"ids": [[]], "distances": [[]], "documents": [[]], "metadatas": [[]], "error": str(e)}

    def delete_document_chunks(self, document_id: str, collection_name: str = DEFAULT_COLLECTION):
        try:
            collection = self.get_or_create_collection(collection_name)
            results = collection.get(where={"document_id": document_id})
            if results and results["ids"]:
                collection.delete(ids=results["ids"])
        except Exception:
            pass

    def delete_by_ids(self, ids: list[str], collection_name: str = DEFAULT_COLLECTION):
        try:
            collection = self.get_or_create_collection(collection_name)
            collection.delete(ids=ids)
        except Exception:
            pass

    def delete_collection(self, name: str = DEFAULT_COLLECTION):
        try:
            client = self._get_client()
            client.delete_collection(name)
        except (ValueError, NotFoundError):
            pass

    def get_collection_stats(self, collection_name: str = DEFAULT_COLLECTION) -> dict:
        try:
            collection = self.get_or_create_collection(collection_name)
            count = collection.count()
            return {"name": collection_name, "count": count}
        except Exception as e:
            return {"name": collection_name, "count": 0, "error": str(e)}


from app.config import settings

vector_store = VectorStore()
