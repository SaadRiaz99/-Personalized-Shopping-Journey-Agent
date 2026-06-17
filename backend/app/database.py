import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.config import settings
from app.models import (
    AuthUser,
    Conversation,
    Document,
    DocumentChunk,
    LoginHistoryEntry,
    Message,
    UserSession,
)

DB_PATH = Path(settings.database_url.replace("sqlite:///", ""))


@contextmanager
def get_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                disabled INTEGER NOT NULL DEFAULT 0,
                email_verified INTEGER NOT NULL DEFAULT 0,
                twofa_enabled INTEGER NOT NULL DEFAULT 0,
                twofa_secret TEXT,
                failed_login_attempts INTEGER NOT NULL DEFAULT 0,
                locked_until TEXT,
                created_at TEXT NOT NULL,
                last_login TEXT
            );

            CREATE TABLE IF NOT EXISTS login_history (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                ip_address TEXT NOT NULL DEFAULT '',
                device_info TEXT NOT NULL DEFAULT '',
                success INTEGER NOT NULL DEFAULT 1,
                fail_reason TEXT,
                timestamp TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS user_sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                refresh_token_hash TEXT NOT NULL,
                device_info TEXT NOT NULL DEFAULT '',
                ip_address TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                last_activity TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_size INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'uploaded',
                chunk_count INTEGER NOT NULL DEFAULT 0,
                error_message TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL DEFAULT 'New Conversation',
                document_ids TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                sources TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL
            );
        """)


def now_iso() -> str:
    return datetime.utcnow().isoformat()


def gen_id() -> str:
    return uuid.uuid4().hex[:12]


# ── Document CRUD ─────────────────────────────────────────────

def create_document(conn, doc: Document) -> None:
    conn.execute(
        "INSERT INTO documents (id, user_id, filename, file_type, file_size, status, chunk_count, error_message, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (doc.id, doc.user_id, doc.filename, doc.file_type, doc.file_size,
         doc.status.value, doc.chunk_count, doc.error_message,
         doc.created_at, doc.updated_at),
    )


def get_document(conn, doc_id: str) -> Optional[Document]:
    row = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
    if row is None:
        return None
    return Document(
        id=row["id"], user_id=row["user_id"], filename=row["filename"],
        file_type=row["file_type"], file_size=row["file_size"],
        status=row["status"], chunk_count=row["chunk_count"],
        error_message=row["error_message"],
        created_at=row["created_at"], updated_at=row["updated_at"],
    )


def list_documents(conn, user_id: Optional[str] = None) -> list[Document]:
    if user_id:
        rows = conn.execute(
            "SELECT * FROM documents WHERE user_id = ? ORDER BY created_at DESC", (user_id,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM documents ORDER BY created_at DESC").fetchall()
    return [_row_to_doc(r) for r in rows]


def update_document(conn, doc: Document) -> None:
    conn.execute(
        "UPDATE documents SET status=?, chunk_count=?, error_message=?, updated_at=? WHERE id=?",
        (doc.status.value, doc.chunk_count, doc.error_message, doc.updated_at, doc.id),
    )


def delete_document(conn, doc_id: str) -> bool:
    cursor = conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    return cursor.rowcount > 0


def count_documents(conn) -> int:
    return conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]


def _row_to_doc(row) -> Document:
    return Document(
        id=row["id"], user_id=row["user_id"], filename=row["filename"],
        file_type=row["file_type"], file_size=row["file_size"],
        status=row["status"], chunk_count=row["chunk_count"],
        error_message=row["error_message"],
        created_at=row["created_at"], updated_at=row["updated_at"],
    )


# ── Document Chunks ───────────────────────────────────────────

def save_chunks(conn, chunks: list[DocumentChunk]) -> None:
    for c in chunks:
        conn.execute(
            "INSERT INTO document_chunks (id, document_id, content, chunk_index, metadata) VALUES (?, ?, ?, ?, ?)",
            (c.id, c.document_id, c.content, c.chunk_index, json.dumps(c.metadata)),
        )


# ── Conversation CRUD ─────────────────────────────────────────

def create_conversation(conn, conv: Conversation) -> None:
    conn.execute(
        "INSERT INTO conversations (id, user_id, title, document_ids, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
        (conv.id, conv.user_id, conv.title, json.dumps(conv.document_ids),
         conv.created_at, conv.updated_at),
    )


def get_conversation(conn, conv_id: str) -> Optional[Conversation]:
    row = conn.execute("SELECT * FROM conversations WHERE id = ?", (conv_id,)).fetchone()
    if row is None:
        return None
    return Conversation(
        id=row["id"], user_id=row["user_id"], title=row["title"],
        document_ids=json.loads(row["document_ids"]),
        created_at=row["created_at"], updated_at=row["updated_at"],
    )


def list_conversations(conn, user_id: str) -> list[Conversation]:
    rows = conn.execute(
        "SELECT * FROM conversations WHERE user_id = ? ORDER BY updated_at DESC", (user_id,)
    ).fetchall()
    return [
        Conversation(
            id=r["id"], user_id=r["user_id"], title=r["title"],
            document_ids=json.loads(r["document_ids"]),
            created_at=r["created_at"], updated_at=r["updated_at"],
        )
        for r in rows
    ]


def update_conversation(conn, conv: Conversation) -> None:
    conn.execute(
        "UPDATE conversations SET title=?, document_ids=?, updated_at=? WHERE id=?",
        (conv.title, json.dumps(conv.document_ids), conv.updated_at, conv.id),
    )


def delete_conversation(conn, conv_id: str) -> bool:
    cursor = conn.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
    conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conv_id,))
    return cursor.rowcount > 0


def count_conversations(conn) -> int:
    return conn.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]


# ── Message CRUD ──────────────────────────────────────────────

def create_message(conn, msg: Message) -> None:
    conn.execute(
        "INSERT INTO messages (id, conversation_id, role, content, sources, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (msg.id, msg.conversation_id, msg.role, msg.content,
         json.dumps(msg.sources), msg.created_at),
    )


def get_messages(conn, conversation_id: str) -> list[Message]:
    rows = conn.execute(
        "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC",
        (conversation_id,),
    ).fetchall()
    return [
        Message(
            id=r["id"], conversation_id=r["conversation_id"],
            role=r["role"], content=r["content"],
            sources=json.loads(r["sources"]),
            created_at=r["created_at"],
        )
        for r in rows
    ]


def count_messages(conn) -> int:
    return conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]


# ── User CRUD ─────────────────────────────────────────────────

def create_user(conn, user: AuthUser) -> None:
    conn.execute(
        "INSERT INTO users (id, username, email, hashed_password, role, disabled, email_verified, twofa_enabled, twofa_secret, failed_login_attempts, locked_until, created_at, last_login) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (user.id, user.username, user.email, user.hashed_password,
         user.role.value, 1 if user.disabled else 0,
         1 if user.email_verified else 0, 1 if user.twofa_enabled else 0,
         user.twofa_secret, user.failed_login_attempts,
         user.locked_until, user.created_at, user.last_login),
    )


def get_user_by_username(conn, username: str) -> Optional[AuthUser]:
    row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    if row is None:
        return None
    return _row_to_auth_user(row)


def get_user_by_id(conn, user_id: str) -> Optional[AuthUser]:
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if row is None:
        return None
    return _row_to_auth_user(row)


def get_user_by_email(conn, email: str) -> Optional[AuthUser]:
    row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if row is None:
        return None
    return _row_to_auth_user(row)


def update_user(conn, user: AuthUser) -> None:
    conn.execute(
        "UPDATE users SET hashed_password=?, role=?, disabled=?, email_verified=?, twofa_enabled=?, twofa_secret=?, failed_login_attempts=?, locked_until=?, last_login=? WHERE id=?",
        (user.hashed_password, user.role.value, 1 if user.disabled else 0,
         1 if user.email_verified else 0, 1 if user.twofa_enabled else 0,
         user.twofa_secret, user.failed_login_attempts, user.locked_until,
         user.last_login, user.id),
    )


def list_users(conn) -> list[AuthUser]:
    rows = conn.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
    return [_row_to_auth_user(r) for r in rows]


def count_users(conn) -> int:
    return conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]


def _row_to_auth_user(row) -> AuthUser:
    return AuthUser(
        id=row["id"], username=row["username"], email=row["email"],
        hashed_password=row["hashed_password"], role=row["role"],
        disabled=bool(row["disabled"]),
        email_verified=bool(row["email_verified"]),
        twofa_enabled=bool(row["twofa_enabled"]),
        twofa_secret=row["twofa_secret"],
        failed_login_attempts=row["failed_login_attempts"],
        locked_until=row["locked_until"],
        created_at=row["created_at"], last_login=row["last_login"],
    )


# ── Login History CRUD ───────────────────────────────────────

def create_login_history(conn, entry: LoginHistoryEntry) -> None:
    conn.execute(
        "INSERT INTO login_history (id, user_id, ip_address, device_info, success, fail_reason, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (entry.id, entry.user_id, entry.ip_address, entry.device_info,
         1 if entry.success else 0, entry.fail_reason, entry.timestamp),
    )


def get_login_history(conn, user_id: str, limit: int = 50) -> list[LoginHistoryEntry]:
    rows = conn.execute(
        "SELECT * FROM login_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
        (user_id, limit),
    ).fetchall()
    return [
        LoginHistoryEntry(
            id=r["id"], user_id=r["user_id"],
            ip_address=r["ip_address"], device_info=r["device_info"],
            success=bool(r["success"]), fail_reason=r["fail_reason"],
            timestamp=r["timestamp"],
        )
        for r in rows
    ]


# ── Session CRUD ─────────────────────────────────────────────

def create_session(conn, session: UserSession) -> None:
    conn.execute(
        "INSERT INTO user_sessions (id, user_id, refresh_token_hash, device_info, ip_address, created_at, last_activity, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (session.id, session.user_id, session.refresh_token_hash,
         session.device_info, session.ip_address,
         session.created_at, session.last_activity,
         1 if session.is_active else 0),
    )


def get_user_sessions(conn, user_id: str) -> list[UserSession]:
    rows = conn.execute(
        "SELECT * FROM user_sessions WHERE user_id = ? AND is_active = 1 ORDER BY last_activity DESC",
        (user_id,),
    ).fetchall()
    return [
        UserSession(
            id=r["id"], user_id=r["user_id"],
            refresh_token_hash=r["refresh_token_hash"],
            device_info=r["device_info"], ip_address=r["ip_address"],
            created_at=r["created_at"], last_activity=r["last_activity"],
            is_active=bool(r["is_active"]),
        )
        for r in rows
    ]


def get_session_by_refresh_hash(conn, hash_val: str) -> Optional[UserSession]:
    row = conn.execute(
        "SELECT * FROM user_sessions WHERE refresh_token_hash = ? AND is_active = 1",
        (hash_val,),
    ).fetchone()
    if row is None:
        return None
    return UserSession(
        id=row["id"], user_id=row["user_id"],
        refresh_token_hash=row["refresh_token_hash"],
        device_info=row["device_info"], ip_address=row["ip_address"],
        created_at=row["created_at"], last_activity=row["last_activity"],
        is_active=bool(row["is_active"]),
    )


def deactivate_session(conn, session_id: str) -> bool:
    cursor = conn.execute(
        "UPDATE user_sessions SET is_active = 0 WHERE id = ?", (session_id,)
    )
    return cursor.rowcount > 0


def deactivate_all_user_sessions(conn, user_id: str) -> None:
    conn.execute(
        "UPDATE user_sessions SET is_active = 0 WHERE user_id = ?", (user_id,)
    )
