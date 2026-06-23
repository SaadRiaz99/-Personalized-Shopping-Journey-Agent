import json
import uuid
from datetime import datetime
from typing import AsyncGenerator, Optional

import httpx

from app.config import settings
from app.database import get_db, get_document, get_messages, create_message
from app.models import Message
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

    if document_ids:
        results = vector_store.search_with_filter(
            query_embedding=query_embedding,
            where={"document_id": {"$in": document_ids}},
            n_results=settings.max_retrieval_docs,
        )
    else:
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
    history = _get_conversation_history(conversation_id)
    answer = await _generate_answer(query, context, history)

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


async def stream_query(
    query: str,
    conversation_id: str,
    user_id: str,
    document_ids: Optional[list[str]] = None,
) -> AsyncGenerator[str, None]:
    query_embeddings = await generate_embeddings([query])
    if not query_embeddings:
        yield json.dumps({"error": "No embeddings generated"})
        return

    query_embedding = query_embeddings[0]

    if document_ids:
        results = vector_store.search_with_filter(
            query_embedding=query_embedding,
            where={"document_id": {"$in": document_ids}},
            n_results=settings.max_retrieval_docs,
        )
    else:
        results = vector_store.search(
            query_embedding=query_embedding,
            n_results=settings.max_retrieval_docs,
        )

    sources = []
    context_chunks = []

    if results and results.get("ids") and results["ids"][0]:
        for i in range(len(results["ids"][0])):
            content = results["documents"][0][i] if results.get("documents") else ""
            metadata = results["metadatas"][0][i] if results.get("metadatas") else {}
            distance = results["distances"][0][i] if results.get("distances") else 0

            with get_db() as conn:
                doc = get_document(conn, metadata.get("document_id", ""))

            source = {
                "chunk_id": results["ids"][0][i],
                "document_id": metadata.get("document_id", ""),
                "document_name": doc.filename if doc else "Unknown",
                "content": content[:500],
                "relevance_score": round(1 - distance, 4) if isinstance(distance, (int, float)) else 0,
            }
            sources.append(source)
            context_chunks.append(content)

    context = "\n\n".join(context_chunks) if context_chunks else ""
    history = _get_conversation_history(conversation_id)
    full_answer = ""

    async for chunk in _stream_answer(query, context, history):
        full_answer += chunk
        yield json.dumps({"type": "token", "content": chunk})

    yield json.dumps({"type": "done", "sources": sources})

    msg = Message(
        id=uuid.uuid4().hex[:12],
        conversation_id=conversation_id,
        role="user",
        content=query,
        sources=[],
        created_at=datetime.utcnow().isoformat(),
    )
    resp_msg = Message(
        id=uuid.uuid4().hex[:12],
        conversation_id=conversation_id,
        role="assistant",
        content=full_answer,
        sources=sources,
        created_at=datetime.utcnow().isoformat(),
    )
    with get_db() as conn:
        create_message(conn, msg)
        create_message(conn, resp_msg)


def _get_conversation_history(conversation_id: str) -> list[dict]:
    with get_db() as conn:
        messages = get_messages(conn, conversation_id)
    history = []
    for msg in messages[-settings.max_conversation_history:]:
        history.append({"role": msg.role, "content": msg.content})
    return history


async def _generate_answer(query: str, context: str, history: list[dict]) -> str:
    if not settings.llm_api_key:
        return _fallback_answer(query, context)

    system_prompt = """You are a helpful AI assistant answering questions based on provided documents.

Guidelines:
- Answer based ONLY on the provided context
- If the context lacks sufficient information, clearly state that
- Cite relevant parts of the context when possible
- Be concise and accurate
- If asked about conversation history, refer to previous messages"""

    messages = [{"role": "system", "content": system_prompt}]
    for h in history[-10:]:
        messages.append(h)
    messages.append({"role": "user", "content": f"Context from documents:\n{context}\n\nQuestion: {query}"})

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
                    "max_tokens": 2048,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error generating answer: {str(e)}"


async def _stream_answer(query: str, context: str, history: list[dict]) -> AsyncGenerator[str, None]:
    if not settings.llm_api_key:
        yield _fallback_answer(query, context)
        return

    system_prompt = """You are a helpful AI assistant answering questions based on provided documents.

Guidelines:
- Answer based ONLY on the provided context
- If the context lacks sufficient information, clearly state that
- Cite relevant parts of the context when possible
- Be concise and accurate"""

    messages = [{"role": "system", "content": system_prompt}]
    for h in history[-10:]:
        messages.append(h)
    messages.append({"role": "user", "content": f"Context from documents:\n{context}\n\nQuestion: {query}"})

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{settings.llm_endpoint}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.llm_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.llm_model,
                    "messages": messages,
                    "temperature": 0.3,
                    "max_tokens": 2048,
                    "stream": True,
                },
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str.strip() == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            delta = data.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue
    except Exception as e:
        yield f"\n[Error: {str(e)}]"


def _fallback_answer(query: str, context: str) -> str:
    if not context:
        return "No relevant documents found. Please upload documents first and try again."
    return f"""Based on the retrieved documents, here is what I found regarding "{query}":

{context[:1500]}

Note: This is a basic response since no LLM API key is configured. Set your LLM_API_KEY in .env for AI-powered answers."""
