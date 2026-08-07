import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

from app.models import (
    Agent,
    AuthUser,
    BudgetEntry,
    BudgetLimit,
    Discount,
    DiscountStack,
    AppliedDiscount,
    LoginHistoryEntry,
    PriceAlertEvent,
    Task,
    UserPrivacyProfile,
    UserSession,
    WishlistItem,
)

DB_PATH = Path(os.environ.get("AGENT_DB_PATH", str(Path(__file__).parents[1] / "agent_store.db")))


@contextmanager
def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
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
            CREATE TABLE IF NOT EXISTS agents (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'idle',
                task TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                type TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                result TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS privacy_profiles (
                user_id TEXT PRIMARY KEY,
                profile_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS discounts (
                id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                product_id TEXT NOT NULL,
                sku TEXT NOT NULL,
                store_price REAL NOT NULL,
                competitor_store TEXT NOT NULL,
                competitor_price REAL NOT NULL,
                discount_amount REAL NOT NULL,
                new_price REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS discount_stacks (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                original_total REAL NOT NULL,
                final_total REAL NOT NULL,
                total_savings REAL NOT NULL,
                applied_discounts TEXT NOT NULL,
                savings_breakdown TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS wishlist_items (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                product_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                product_price REAL NOT NULL,
                product_category TEXT NOT NULL,
                product_image TEXT,
                note TEXT,
                price_alert_threshold REAL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS price_alerts (
                id TEXT PRIMARY KEY,
                wishlist_item_id TEXT NOT NULL,
                product_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                current_price REAL NOT NULL,
                target_price REAL NOT NULL,
                triggered_at TEXT NOT NULL,
                notified INTEGER NOT NULL DEFAULT 0
            );

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

            CREATE TABLE IF NOT EXISTS budget_entries (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                product_id TEXT NOT NULL,
                product_name TEXT NOT NULL,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 1,
                timestamp TEXT NOT NULL,
                note TEXT
            );

            CREATE TABLE IF NOT EXISTS budget_limits (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                period TEXT NOT NULL,
                limit_amount REAL NOT NULL,
                category TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
        """)


# ── Agent CRUD ──────────────────────────────────────────────

def create_agent(conn, agent: Agent) -> None:
    conn.execute(
        "INSERT INTO agents (id, name, status, task, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
        (agent.id, agent.name, agent.status.value, agent.task,
         agent.created_at.isoformat(), agent.updated_at.isoformat()),
    )


def get_agent(conn, agent_id: str) -> Optional[Agent]:
    row = conn.execute("SELECT * FROM agents WHERE id = ?", (agent_id,)).fetchone()
    if row is None:
        return None
    return Agent(
        id=row["id"], name=row["name"], status=row["status"],
        task=row["task"],
        created_at=row["created_at"], updated_at=row["updated_at"],
    )


def list_agents(conn) -> list[Agent]:
    rows = conn.execute("SELECT * FROM agents").fetchall()
    return [
        Agent(
            id=r["id"], name=r["name"], status=r["status"],
            task=r["task"],
            created_at=r["created_at"], updated_at=r["updated_at"],
        )
        for r in rows
    ]


def delete_agent(conn, agent_id: str) -> bool:
    cursor = conn.execute("DELETE FROM agents WHERE id = ?", (agent_id,))
    return cursor.rowcount > 0


def update_agent(conn, agent: Agent) -> None:
    conn.execute(
        "UPDATE agents SET name=?, status=?, task=?, updated_at=? WHERE id=?",
        (agent.name, agent.status.value, agent.task,
         agent.updated_at.isoformat(), agent.id),
    )


# ── Task CRUD ───────────────────────────────────────────────

def create_task(conn, task: Task) -> None:
    conn.execute(
        "INSERT INTO tasks (id, agent_id, type, status, result, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (task.id, task.agent_id, task.type, task.status.value, task.result,
         task.created_at.isoformat(), task.updated_at.isoformat()),
    )


def list_tasks(conn) -> list[Task]:
    rows = conn.execute("SELECT * FROM tasks").fetchall()
    return [
        Task(
            id=r["id"], agent_id=r["agent_id"], type=r["type"],
            status=r["status"], result=r["result"],
            created_at=r["created_at"], updated_at=r["updated_at"],
        )
        for r in rows
    ]


# ── Privacy Profile CRUD ───────────────────────────────────

def get_privacy_profile(conn, user_id: str) -> Optional[UserPrivacyProfile]:
    row = conn.execute(
        "SELECT profile_json FROM privacy_profiles WHERE user_id = ?", (user_id,)
    ).fetchone()
    if row is None:
        return None
    return UserPrivacyProfile.model_validate(json.loads(row["profile_json"]))


def upsert_privacy_profile(conn, user_id: str, profile: UserPrivacyProfile) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO privacy_profiles (user_id, profile_json) VALUES (?, ?)",
        (user_id, json.dumps(profile.model_dump(mode="json"))),
    )


def delete_privacy_profile(conn, user_id: str) -> bool:
    cursor = conn.execute(
        "DELETE FROM privacy_profiles WHERE user_id = ?", (user_id,)
    )
    return cursor.rowcount > 0


# ── Discount CRUD ──────────────────────────────────────────

def create_discount(conn, discount: Discount) -> None:
    conn.execute(
        "INSERT INTO discounts (id, agent_id, product_id, sku, store_price, competitor_store, competitor_price, discount_amount, new_price, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (discount.id, discount.agent_id, discount.product_id,
         discount.sku, discount.store_price, discount.competitor_store,
         discount.competitor_price, discount.discount_amount,
         discount.new_price, discount.status.value,
         discount.created_at.isoformat()),
    )


def get_discount(conn, discount_id: str) -> Optional[Discount]:
    row = conn.execute(
        "SELECT * FROM discounts WHERE id = ?", (discount_id,)
    ).fetchone()
    if row is None:
        return None
    return Discount(
        id=row["id"], agent_id=row["agent_id"],
        product_id=row["product_id"], sku=row["sku"],
        store_price=row["store_price"],
        competitor_store=row["competitor_store"],
        competitor_price=row["competitor_price"],
        discount_amount=row["discount_amount"],
        new_price=row["new_price"], status=row["status"],
        created_at=row["created_at"],
    )


def list_discounts(conn) -> list[Discount]:
    rows = conn.execute("SELECT * FROM discounts").fetchall()
    return [
        Discount(
            id=r["id"], agent_id=r["agent_id"],
            product_id=r["product_id"], sku=r["sku"],
            store_price=r["store_price"],
            competitor_store=r["competitor_store"],
            competitor_price=r["competitor_price"],
            discount_amount=r["discount_amount"],
            new_price=r["new_price"], status=r["status"],
            created_at=r["created_at"],
        )
        for r in rows
    ]


def update_discount(conn, discount: Discount) -> None:
    conn.execute(
        "UPDATE discounts SET agent_id=?, product_id=?, sku=?, store_price=?, competitor_store=?, competitor_price=?, discount_amount=?, new_price=?, status=? WHERE id=?",
        (discount.agent_id, discount.product_id, discount.sku,
         discount.store_price, discount.competitor_store,
         discount.competitor_price, discount.discount_amount,
         discount.new_price, discount.status.value, discount.id),
    )


# ── Discount Stack CRUD ────────────────────────────────────

def create_stack(conn, stack: DiscountStack) -> None:
    conn.execute(
        "INSERT INTO discount_stacks (id, user_id, original_total, final_total, total_savings, applied_discounts, savings_breakdown, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (stack.id, stack.user_id, stack.original_total,
         stack.final_total, stack.total_savings,
         json.dumps([d.model_dump(mode="json") for d in stack.applied_discounts]),
         stack.savings_breakdown, stack.created_at.isoformat()),
    )


def get_stack(conn, stack_id: str) -> Optional[DiscountStack]:
    row = conn.execute(
        "SELECT * FROM discount_stacks WHERE id = ?", (stack_id,)
    ).fetchone()
    if row is None:
        return None
    return DiscountStack(
        id=row["id"], user_id=row["user_id"],
        original_total=row["original_total"],
        final_total=row["final_total"],
        total_savings=row["total_savings"],
        applied_discounts=[
            AppliedDiscount.model_validate(d)
            for d in json.loads(row["applied_discounts"])
        ],
        savings_breakdown=row["savings_breakdown"],
        created_at=row["created_at"],
    )


def list_stacks(conn) -> list[DiscountStack]:
    rows = conn.execute("SELECT * FROM discount_stacks").fetchall()
    return [
        DiscountStack(
            id=r["id"], user_id=r["user_id"],
            original_total=r["original_total"],
            final_total=r["final_total"],
            total_savings=r["total_savings"],
            applied_discounts=[
                AppliedDiscount.model_validate(d)
                for d in json.loads(r["applied_discounts"])
            ],
            savings_breakdown=r["savings_breakdown"],
            created_at=r["created_at"],
        )
        for r in rows
    ]


# ── Wishlist CRUD ───────────────────────────────────────────

def create_wishlist_item(conn, item: WishlistItem) -> None:
    conn.execute(
        "INSERT INTO wishlist_items (id, user_id, product_id, product_name, product_price, product_category, product_image, note, price_alert_threshold, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (item.id, item.user_id, item.product_id, item.product_name,
         item.product_price, item.product_category, item.product_image,
         item.note, item.price_alert_threshold, item.created_at),
    )


def get_wishlist(conn, user_id: str) -> list[WishlistItem]:
    rows = conn.execute(
        "SELECT * FROM wishlist_items WHERE user_id = ? ORDER BY created_at DESC", (user_id,)
    ).fetchall()
    return [
        WishlistItem(
            id=r["id"], user_id=r["user_id"],
            product_id=r["product_id"], product_name=r["product_name"],
            product_price=r["product_price"], product_category=r["product_category"],
            product_image=r["product_image"], note=r["note"],
            price_alert_threshold=r["price_alert_threshold"],
            created_at=r["created_at"],
        )
        for r in rows
    ]


def delete_wishlist_item(conn, item_id: str) -> bool:
    cursor = conn.execute("DELETE FROM wishlist_items WHERE id = ?", (item_id,))
    return cursor.rowcount > 0


def update_wishlist_item(conn, item: WishlistItem) -> None:
    conn.execute(
        "UPDATE wishlist_items SET note=?, price_alert_threshold=? WHERE id=?",
        (item.note, item.price_alert_threshold, item.id),
    )


def get_wishlist_item(conn, item_id: str) -> Optional[WishlistItem]:
    row = conn.execute("SELECT * FROM wishlist_items WHERE id = ?", (item_id,)).fetchone()
    if row is None:
        return None
    return WishlistItem(
        id=row["id"], user_id=row["user_id"],
        product_id=row["product_id"], product_name=row["product_name"],
        product_price=row["product_price"], product_category=row["product_category"],
        product_image=row["product_image"], note=row["note"],
        price_alert_threshold=row["price_alert_threshold"],
        created_at=row["created_at"],
    )


# ── Price Alert CRUD ────────────────────────────────────────

def create_price_alert(conn, alert: PriceAlertEvent) -> None:
    conn.execute(
        "INSERT INTO price_alerts (id, wishlist_item_id, product_id, product_name, current_price, target_price, triggered_at, notified) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (alert.id, alert.wishlist_item_id, alert.product_id,
         alert.product_name, alert.current_price, alert.target_price,
         alert.triggered_at, 1 if alert.notified else 0),
    )


def list_price_alerts(conn, user_id: str) -> list[PriceAlertEvent]:
    rows = conn.execute(
        """SELECT a.* FROM price_alerts a
           JOIN wishlist_items w ON a.wishlist_item_id = w.id
           WHERE w.user_id = ? ORDER BY a.triggered_at DESC""",
        (user_id,),
    ).fetchall()
    return [
        PriceAlertEvent(
            id=r["id"], wishlist_item_id=r["wishlist_item_id"],
            product_id=r["product_id"], product_name=r["product_name"],
            current_price=r["current_price"], target_price=r["target_price"],
            triggered_at=r["triggered_at"], notified=bool(r["notified"]),
        )
        for r in rows
    ]


# ── Auth CRUD ────────────────────────────────────────────────

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


# ── Budget Entry CRUD ─────────────────────────────────────────

def create_budget_entry(conn, entry: BudgetEntry) -> None:
    conn.execute(
        "INSERT INTO budget_entries (id, user_id, product_id, product_name, category, amount, quantity, timestamp, note) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (entry.id, entry.user_id, entry.product_id, entry.product_name,
         entry.category, entry.amount, entry.quantity, entry.timestamp,
         entry.note),
    )


def get_budget_entries(conn, user_id: str, since: Optional[str] = None) -> list[BudgetEntry]:
    if since:
        rows = conn.execute(
            "SELECT * FROM budget_entries WHERE user_id = ? AND timestamp >= ? ORDER BY timestamp DESC",
            (user_id, since),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM budget_entries WHERE user_id = ? ORDER BY timestamp DESC",
            (user_id,),
        ).fetchall()
    return [
        BudgetEntry(
            id=r["id"], user_id=r["user_id"],
            product_id=r["product_id"], product_name=r["product_name"],
            category=r["category"], amount=r["amount"],
            quantity=r["quantity"], timestamp=r["timestamp"],
            note=r["note"],
        )
        for r in rows
    ]


def delete_budget_entry(conn, entry_id: str) -> bool:
    cursor = conn.execute("DELETE FROM budget_entries WHERE id = ?", (entry_id,))
    return cursor.rowcount > 0


# ── Budget Limit CRUD ──────────────────────────────────────────

def create_budget_limit(conn, limit: BudgetLimit) -> None:
    conn.execute(
        "INSERT INTO budget_limits (id, user_id, period, limit_amount, category, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (limit.id, limit.user_id, limit.period.value, limit.limit_amount,
         limit.category, limit.created_at, limit.updated_at),
    )


def get_budget_limits(conn, user_id: str) -> list[BudgetLimit]:
    rows = conn.execute(
        "SELECT * FROM budget_limits WHERE user_id = ?", (user_id,)
    ).fetchall()
    return [
        BudgetLimit(
            id=r["id"], user_id=r["user_id"],
            period=r["period"], limit_amount=r["limit_amount"],
            category=r["category"],
            created_at=r["created_at"], updated_at=r["updated_at"],
        )
        for r in rows
    ]


def update_budget_limit(conn, limit: BudgetLimit) -> None:
    conn.execute(
        "UPDATE budget_limits SET limit_amount=?, category=?, updated_at=? WHERE id=?",
        (limit.limit_amount, limit.category, limit.updated_at, limit.id),
    )


def delete_budget_limit(conn, limit_id: str) -> bool:
    cursor = conn.execute("DELETE FROM budget_limits WHERE id = ?", (limit_id,))
    return cursor.rowcount > 0
