import os
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
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
)
from app.models import Document, DocumentStatus, UserRole

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

    return {"message": "File uploaded", "document": doc.model_dump()}


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


@router.delete("/{doc_id}")
async def delete_document_endpoint(doc_id: str, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        doc = get_document(conn, doc_id)
        if doc is None:
            raise HTTPException(status_code=404, detail="Document not found")
        if doc.user_id != current_user["id"] and current_user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Access denied")
        delete_document(conn, doc_id)

    file_path = Path(settings.upload_dir) / f"{doc_id}.{doc.file_type}"
    if file_path.exists():
        file_path.unlink()

    return {"message": "Document deleted"}
