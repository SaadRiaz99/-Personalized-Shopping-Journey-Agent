import uuid
from datetime import datetime
from typing import Optional

import httpx

from app.config import settings
from app.database import get_db, get_document, create_message
from app.models import DocumentChunk, Message
from app.services.embedding_service import generate_embeddings
from app.services.vector_store import vector_store


async def process_query(
    query: str,
    conversation_id: str,
    user_id: str,
    document_ids: Optional[list[str]] = None,
) -> dict:
    query_embeddings = await generate_embeddings([query])
    if not query_embeddings:
        return {"message": "No embeddings generated. Check your API key.", "sources": []}

    query_embedding = query_embeddings[0]

    results = vector_store.search(
        query_embedding=query_embedding,
        n_results=settings.max_retrieval_docs,
    )

    sources = []
    context_chunks = []

    if results and results.get("ids") and results["ids"][0]:
        for i in range(len(results["ids"][0])):
            chunk_id = results["ids"][0][i]
            content = results["documents"][0][i] if results.get("documents") else ""
            metadata = results["metadatas"][0][i] if results.get("metadatas") else {}
            distance = results["distances"][0][i] if results.get("distances") else 0

            if document_ids:
                doc_id = metadata.get("document_id", "")
                if doc_id not in document_ids:
                    continue

            with get_db() as conn:
                doc = get_document(conn, metadata.get("document_id", ""))

            source = {
                "chunk_id": chunk_id,
                "document_id": metadata.get("document_id", ""),
                "document_name": doc.filename if doc else "Unknown",
                "content": content[:500],
                "relevance_score": round(1 - distance, 4) if isinstance(distance, (int, float)) else 0,
            }
            sources.append(source)
            context_chunks.append(content)

    context = "\n\n".join(context_chunks) if context_chunks else ""
    answer = await _generate_answer(query, context)

    msg = Message(
        id=uuid.uuid4().hex[:12],
        conversation_id=conversation_id,
        role="user",
        content=query,
        sources=[],
        created_at=datetime.utcnow().isoformat(),
    )
    with get_db() as conn:
        create_message(conn, msg)

    resp_msg = Message(
        id=uuid.uuid4().hex[:12],
        conversation_id=conversation_id,
        role="assistant",
        content=answer,
        sources=sources,
        created_at=datetime.utcnow().isoformat(),
    )
    with get_db() as conn:
        create_message(conn, resp_msg)

    return {"message": answer, "conversation_id": conversation_id, "sources": sources}


async def _generate_answer(query: str, context: str) -> str:
    if not settings.llm_api_key:
        return _fallback_answer(query, context)

    system_prompt = """You are a helpful assistant that answers questions based on the provided context.
Use only the context to answer. If the context does not contain enough information, say so.
Cite specific parts of the context when possible."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"},
    ]

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{settings.llm_endpoint}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.llm_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.llm_model,
                    "messages": messages,
                    "temperature": 0.3,
                    "max_tokens": 1024,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error generating answer: {str(e)}"


def _fallback_answer(query: str, context: str) -> str:
    if not context:
        return "No relevant documents found. Please upload documents first and try again."
    return f"""Based on the retrieved documents, here is what I found regarding "{query}":

{context[:1000]}

Note: This is a basic response since no LLM API key is configured. Set your LLM_API_KEY in .env for AI-powered answers."""
