import os
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse

from app.auth import get_current_user, require_role
from app.config import settings
from app.database import (
    get_db,
    create_document,
    get_document,
    list_documents,
    update_document,
    delete_document,
    get_user_by_id,
    save_chunks,
)
from app.models import Document, DocumentStatus, DocumentChunk, UserRole
from app.services.document_processor import extract_text, chunk_text
from app.services.embedding_service import generate_embeddings
from app.services.vector_store import vector_store

router = APIRouter(prefix="/api/documents", tags=["documents"])

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
MAX_FILE_SIZE = settings.max_file_size_mb * 1024 * 1024


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type {ext} not supported")

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"File too large (max {settings.max_file_size_mb}MB)")

    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    doc_id = uuid.uuid4().hex[:12]
    safe_filename = f"{doc_id}{ext}"
    file_path = upload_dir / safe_filename

    with open(file_path, "wb") as f:
        f.write(contents)

    doc = Document(
        id=doc_id,
        user_id=current_user["id"],
        filename=file.filename,
        file_type=ext[1:],
        file_size=len(contents),
        status=DocumentStatus.uploaded,
        created_at=datetime.utcnow().isoformat(),
        updated_at=datetime.utcnow().isoformat(),
    )

    with get_db() as conn:
        create_document(conn, doc)

    try:
        text = extract_text(str(file_path), doc.file_type)
        chunk_data = chunk_text(text)

        chunks = []
        for c in chunk_data:
            chunk = DocumentChunk(
                id=uuid.uuid4().hex[:12],
                document_id=doc_id,
                content=c["content"],
                chunk_index=c["chunk_index"],
                metadata={"document_id": doc_id, "filename": doc.filename, "chunk_index": c["chunk_index"]},
            )
            chunks.append(chunk)

        texts_for_embedding = [c.content for c in chunks]
        embeddings = await generate_embeddings(texts_for_embedding)

        if embeddings and len(embeddings) == len(chunks):
            vector_chunks = []
            for i, chunk in enumerate(chunks):
                vector_chunks.append({
                    "id": chunk.id,
                    "content": chunk.content,
                    "metadata": chunk.metadata,
                })
            vector_store.add_chunks(vector_chunks, embeddings)

        with get_db() as conn:
            save_chunks(conn, chunks)
            doc.status = DocumentStatus.processed
            doc.chunk_count = len(chunks)
            doc.updated_at = datetime.utcnow().isoformat()
            update_document(conn, doc)

    except Exception as e:
        with get_db() as conn:
            doc.status = DocumentStatus.error
            doc.error_message = str(e)
            doc.updated_at = datetime.utcnow().isoformat()
            update_document(conn, doc)

    return {"message": "File uploaded and processed", "document": doc.model_dump()}


@router.get("")
async def list_all_documents(current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        docs = list_documents(conn, user_id=current_user["id"])
    return {"documents": [d.model_dump() for d in docs], "total": len(docs)}


@router.get("/{doc_id}")
async def get_document_details(doc_id: str, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        doc = get_document(conn, doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.user_id != current_user["id"] and current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    return {"document": doc.model_dump()}


@router.post("/{doc_id}/process")
async def process_document(doc_id: str, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        doc = get_document(conn, doc_id)
        if doc is None:
            raise HTTPException(status_code=404, detail="Document not found")
        if doc.user_id != current_user["id"] and current_user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Access denied")

        doc.status = DocumentStatus.processing
        update_document(conn, doc)

    file_path = Path(settings.upload_dir) / f"{doc_id}.{doc.file_type}"
    if not file_path.exists():
        with get_db() as conn:
            doc.status = DocumentStatus.error
            doc.error_message = "File not found on disk"
            update_document(conn, doc)
        raise HTTPException(status_code=404, detail="File not found on disk")

    try:
        text = extract_text(str(file_path), doc.file_type)
        chunk_data = chunk_text(text)

        chunks = []
        for c in chunk_data:
            chunk = DocumentChunk(
                id=uuid.uuid4().hex[:12],
                document_id=doc_id,
                content=c["content"],
                chunk_index=c["chunk_index"],
                metadata={"document_id": doc_id, "filename": doc.filename, "chunk_index": c["chunk_index"]},
            )
            chunks.append(chunk)

        texts_for_embedding = [c.content for c in chunks]
        embeddings = await generate_embeddings(texts_for_embedding)

        if embeddings and len(embeddings) == len(chunks):
            vector_chunks = []
            for i, chunk in enumerate(chunks):
                vector_chunks.append({
                    "id": chunk.id,
                    "content": chunk.content,
                    "metadata": chunk.metadata,
                })
            vector_store.add_chunks(vector_chunks, embeddings)

        with get_db() as conn:
            save_chunks(conn, chunks)
            doc.status = DocumentStatus.processed
            doc.chunk_count = len(chunks)
            doc.updated_at = datetime.utcnow().isoformat()
            update_document(conn, doc)

        return {"message": "Document processed", "chunk_count": len(chunks)}

    except Exception as e:
        with get_db() as conn:
            doc.status = DocumentStatus.error
            doc.error_message = str(e)
            doc.updated_at = datetime.utcnow().isoformat()
            update_document(conn, doc)
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.get("/{doc_id}/chunks")
async def get_document_chunks(doc_id: str, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        doc = get_document(conn, doc_id)
        if doc is None:
            raise HTTPException(status_code=404, detail="Document not found")
        if doc.user_id != current_user["id"] and current_user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Access denied")
        rows = conn.execute(
            "SELECT id, document_id, content, chunk_index, metadata FROM document_chunks WHERE document_id = ? ORDER BY chunk_index",
            (doc_id,),
        ).fetchall()
    chunks = [
        {"id": r["id"], "document_id": r["document_id"], "content": r["content"],
         "chunk_index": r["chunk_index"], "metadata": r["metadata"]}
        for r in rows
    ]
    return {"chunks": chunks, "total": len(chunks)}


@router.delete("/{doc_id}")
async def delete_document_endpoint(doc_id: str, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        doc = get_document(conn, doc_id)
        if doc is None:
            raise HTTPException(status_code=404, detail="Document not found")
        if doc.user_id != current_user["id"] and current_user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Access denied")
        conn.execute("DELETE FROM document_chunks WHERE document_id = ?", (doc_id,))
        delete_document(conn, doc_id)

    vector_store.delete_document_chunks(doc_id)

    file_path = Path(settings.upload_dir) / f"{doc_id}.{doc.file_type}"
    if file_path.exists():
        file_path.unlink()

    return {"message": "Document deleted"}
