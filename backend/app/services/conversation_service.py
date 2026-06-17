from app.database import get_db, get_messages, get_conversation
from app.config import settings


def get_conversation_context(conversation_id: str) -> list[dict]:
    with get_db() as conn:
        messages = get_messages(conn, conversation_id)
    history = []
    for msg in messages[-settings.max_conversation_history:]:
        history.append({"role": msg.role, "content": msg.content})
    return history
