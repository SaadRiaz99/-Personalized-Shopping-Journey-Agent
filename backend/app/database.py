import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

from app.models import (
    Agent,
    Discount,
    DiscountStack,
    AppliedDiscount,
    Task,
    UserPrivacyProfile,
)

DB_PATH = Path(__file__).parents[1] / "agent_store.db"


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
