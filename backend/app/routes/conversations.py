from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from app.auth import get_current_user
from app.database import (
    get_db,
    create_conversation,
    get_conversation,
    list_conversations,
    update_conversation,
    delete_conversation,
    get_messages,
)
from app.models import Conversation, ConversationCreate, ConversationUpdate

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.get("")
async def list_user_conversations(current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        convs = list_conversations(conn, current_user["id"])
    return {"conversations": [c.model_dump() for c in convs], "total": len(convs)}


@router.post("")
async def create_new_conversation(body: ConversationCreate, current_user: dict = Depends(get_current_user)):
    conv = Conversation(
        id=__import__("uuid").uuid4().hex[:12],
        user_id=current_user["id"],
        title=body.title,
        document_ids=body.document_ids,
        created_at=datetime.utcnow().isoformat(),
        updated_at=datetime.utcnow().isoformat(),
    )
    with get_db() as conn:
        create_conversation(conn, conv)
    return {"conversation": conv.model_dump()}


@router.get("/{conv_id}")
async def get_conversation_details(conv_id: str, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        conv = get_conversation(conn, conv_id)
        if conv is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
        if conv.user_id != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        messages = get_messages(conn, conv_id)
    return {"conversation": conv.model_dump(), "messages": [m.model_dump() for m in messages]}


@router.patch("/{conv_id}")
async def update_conversation_title(conv_id: str, body: ConversationUpdate, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        conv = get_conversation(conn, conv_id)
        if conv is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
        if conv.user_id != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        if body.title is not None:
            conv.title = body.title
        conv.updated_at = datetime.utcnow().isoformat()
        update_conversation(conn, conv)
    return {"conversation": conv.model_dump()}


@router.delete("/{conv_id}")
async def delete_conversation_endpoint(conv_id: str, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        conv = get_conversation(conn, conv_id)
        if conv is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
        if conv.user_id != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        delete_conversation(conn, conv_id)
    return {"message": "Conversation deleted"}
