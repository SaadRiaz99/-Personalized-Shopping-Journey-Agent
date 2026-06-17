import os
from pathlib import Path
from typing import Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings


class VectorStore:
    _instance: Optional["VectorStore"] = None
    _client: Optional[chromadb.ClientAPI] = None

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

    def get_or_create_collection(self, name: str = "documents"):
        client = self._get_client()
        try:
            return client.get_collection(name)
        except ValueError:
            return client.create_collection(name)

    def add_chunks(self, chunks: list[dict], embeddings: list[list[float]], collection_name: str = "documents"):
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

    def search(self, query_embedding: list[float], n_results: int = 5, collection_name: str = "documents") -> dict:
        collection = self.get_or_create_collection(collection_name)
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
        )
        return results

    def delete_document_chunks(self, document_id: str, collection_name: str = "documents"):
        collection = self.get_or_create_collection(collection_name)
        results = collection.get(where={"document_id": document_id})
        if results and results["ids"]:
            collection.delete(ids=results["ids"])

    def delete_collection(self, name: str = "documents"):
        client = self._get_client()
        try:
            client.delete_collection(name)
        except ValueError:
            pass

    def get_collection_stats(self, collection_name: str = "documents") -> dict:
        try:
            collection = self.get_or_create_collection(collection_name)
            count = collection.count()
            return {"name": collection_name, "count": count}
        except Exception as e:
            return {"name": collection_name, "count": 0, "error": str(e)}


vector_store = VectorStore()
