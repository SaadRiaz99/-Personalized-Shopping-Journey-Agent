from fastapi import APIRouter, Depends, HTTPException

from app.auth import get_current_user, require_role
from app.database import get_db, count_users, count_documents, count_conversations, count_messages, list_documents, list_users, update_user, get_user_by_id
from app.models import UserRole
from app.config import settings

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/stats")
async def get_admin_stats(current_user: dict = Depends(require_role(UserRole.admin))):
    with get_db() as conn:
        total_users = count_users(conn)
        total_documents = count_documents(conn)
        total_conversations = count_conversations(conn)
        total_messages = count_messages(conn)

        docs = list_documents(conn)
        docs_by_type = {}
        total_size = 0
        for d in docs:
            docs_by_type[d.file_type] = docs_by_type.get(d.file_type, 0) + 1
            total_size += d.file_size

    return {
        "total_users": total_users,
        "total_documents": total_documents,
        "total_conversations": total_conversations,
        "total_messages": total_messages,
        "documents_by_type": docs_by_type,
        "storage_used_mb": round(total_size / (1024 * 1024), 2),
    }


@router.get("/users")
async def get_all_users(current_user: dict = Depends(require_role(UserRole.admin))):
    with get_db() as conn:
        users = list_users(conn)
    return {"users": [u.model_dump() for u in users], "total": len(users)}


@router.patch("/users/{user_id}")
async def update_user_admin(user_id: str, body: dict, current_user: dict = Depends(require_role(UserRole.admin))):
    with get_db() as conn:
        user = get_user_by_id(conn, user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        if "role" in body:
            try:
                user.role = UserRole(body["role"])
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid role")
        if "disabled" in body:
            user.disabled = bool(body["disabled"])
        update_user(conn, user)
    return {"message": "User updated", "user": user.model_dump()}
