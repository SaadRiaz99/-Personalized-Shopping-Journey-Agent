import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.auth import get_current_user
from app.database import get_db, create_conversation, get_conversation, create_message, get_messages
from app.models import ChatRequest, Conversation, Message
from app.services.rag_service import process_query, stream_query

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/send")
async def send_message(body: ChatRequest, current_user: dict = Depends(get_current_user)):
    conversation_id = body.conversation_id

    if not conversation_id:
        conversation_id = uuid.uuid4().hex[:12]
        conv = Conversation(
            id=conversation_id,
            user_id=current_user["id"],
            title=body.message[:80] + ("..." if len(body.message) > 80 else ""),
            document_ids=body.document_ids,
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat(),
        )
        with get_db() as conn:
            create_conversation(conn, conv)
    else:
        with get_db() as conn:
            conv = get_conversation(conn, conversation_id)
            if conv is None:
                raise HTTPException(status_code=404, detail="Conversation not found")
            if conv.user_id != current_user["id"]:
                raise HTTPException(status_code=403, detail="Access denied")

    result = await process_query(
        query=body.message,
        conversation_id=conversation_id,
        user_id=current_user["id"],
        document_ids=body.document_ids or None,
    )

    return {
        "message": result["message"],
        "conversation_id": conversation_id,
        "sources": result["sources"],
    }


@router.post("/stream")
async def stream_message(body: ChatRequest, current_user: dict = Depends(get_current_user)):
    conversation_id = body.conversation_id

    if not conversation_id:
        conversation_id = uuid.uuid4().hex[:12]
        conv = Conversation(
            id=conversation_id,
            user_id=current_user["id"],
            title=body.message[:80] + ("..." if len(body.message) > 80 else ""),
            document_ids=body.document_ids,
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat(),
        )
        with get_db() as conn:
            create_conversation(conn, conv)

    return StreamingResponse(
        stream_query(
            query=body.message,
            conversation_id=conversation_id,
            user_id=current_user["id"],
            document_ids=body.document_ids or None,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/{conversation_id}/messages")
async def get_conversation_messages(conversation_id: str, current_user: dict = Depends(get_current_user)):
    with get_db() as conn:
        conv = get_conversation(conn, conversation_id)
        if conv is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
        if conv.user_id != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied")
        messages = get_messages(conn, conversation_id)
    return {"messages": [m.model_dump() for m in messages], "total": len(messages)}
