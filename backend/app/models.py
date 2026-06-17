from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    admin = "admin"
    premium = "premium"
    user = "user"


class AuthUser(BaseModel):
    id: str
    username: str
    email: str
    hashed_password: str
    role: UserRole = UserRole.user
    disabled: bool = False
    email_verified: bool = False
    twofa_enabled: bool = False
    twofa_secret: Optional[str] = None
    failed_login_attempts: int = 0
    locked_until: Optional[str] = None
    created_at: str = ""
    last_login: Optional[str] = None


class LoginHistoryEntry(BaseModel):
    id: str
    user_id: str
    ip_address: str
    device_info: str
    success: bool
    fail_reason: Optional[str] = None
    timestamp: str


class UserSession(BaseModel):
    id: str
    user_id: str
    refresh_token_hash: str
    device_info: str
    ip_address: str
    created_at: str
    last_activity: str
    is_active: bool = True


class DocumentStatus(str, Enum):
    uploaded = "uploaded"
    processing = "processing"
    processed = "processed"
    error = "error"


class Document(BaseModel):
    id: str
    user_id: str
    filename: str
    file_type: str
    file_size: int
    status: DocumentStatus = DocumentStatus.uploaded
    chunk_count: int = 0
    error_message: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""


class DocumentChunk(BaseModel):
    id: str
    document_id: str
    content: str
    chunk_index: int
    metadata: dict = {}


class Conversation(BaseModel):
    id: str
    user_id: str
    title: str = "New Conversation"
    document_ids: list[str] = []
    created_at: str = ""
    updated_at: str = ""


class Message(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    sources: list[dict] = []
    created_at: str = ""


class ChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    message: str
    document_ids: list[str] = []


class ChatResponse(BaseModel):
    message: str
    conversation_id: str
    sources: list[dict] = []


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=32)
    email: str = Field(..., min_length=5, max_length=128)
    password: str = Field(..., min_length=8, max_length=128)


class LoginRequest(BaseModel):
    username: str
    password: str
    twofa_code: Optional[str] = None
    device_info: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class RefreshRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class ConversationCreate(BaseModel):
    title: str = "New Conversation"
    document_ids: list[str] = []


class ConversationUpdate(BaseModel):
    title: Optional[str] = None


class AdminStats(BaseModel):
    total_users: int
    total_documents: int
    total_conversations: int
    total_messages: int
    total_chunks: int
    documents_by_type: dict
    storage_used_mb: float
