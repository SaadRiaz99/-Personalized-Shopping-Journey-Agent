"""
session_memory.py
-----------------
In-memory conversation session store.
- Implements the agents.Session protocol so Runner uses it natively.
- Stores conversation history per session_id.
- Tracks seen product IDs and user preferences within each session.
"""

from __future__ import annotations
import time                                          # For session age tracking
from typing import Optional
from agents import TResponseInputItem                # Type for history items
from agents.memory import Session                    # Protocol that Runner expects


class InMemorySession:
    """
    Thread-safe in-memory session for one conversation.

    Usage:
        session = InMemorySession(session_id="user-42")
        result  = await Runner.run(agent, input=msg, session=session)
    """

    def __init__(self, session_id: str, max_history: int = 40):
        self.session_id:       str                     = session_id   # Unique key
        self._history:         list[TResponseInputItem] = []           # Message history
        self._max_history:     int                     = max_history   # Rolling window

        # Extra metadata (not part of the Session protocol)
        self.seen_ids:         set[int]                = set()        # Products already shown
        self.preferences:      dict                    = {}           # e.g. {"budget": "200"}
        self.created_at:       float                   = time.time()  # Session birth time
        self.turn_count:       int                     = 0            # Number of exchanges
        # Pagination: remember last search params for "show me more"
        self.last_search_params: dict | None = None

    # ── Session protocol methods ──────────────────────────────────────────────
    async def get_items(self, limit: Optional[int] = None) -> list[TResponseInputItem]:
        """Return conversation history, optionally only the last N items."""
        if limit is None:
            return list(self._history)
        return list(self._history[-limit:])

    async def add_items(self, items: list[TResponseInputItem]) -> None:
        """Append new messages to history and trim if over max_history."""
        self._history.extend(items)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]
        self.turn_count += 1

    async def pop_item(self) -> Optional[TResponseInputItem]:
        """Remove and return the most recent history item."""
        if self._history:
            return self._history.pop()
        return None

    async def clear_session(self) -> None:
        """Reset everything — history, seen IDs, preferences, and turn count."""
        self._history.clear()
        self.seen_ids.clear()
        self.preferences.clear()
        self.turn_count = 0

    # ── Extra helpers used by tools ───────────────────────────────────────────
    def update_last_search(self, params: dict) -> None:
        """Save the last search parameters for pagination."""
        self.last_search_params = dict(params)

    def get_last_search(self) -> dict | None:
        """Return the last search params (None if no search yet)."""
        return self.last_search_params

    def mark_seen(self, product_ids: list[int]) -> None:
        """Record that these product IDs were shown to the user."""
        self.seen_ids.update(product_ids)

    def update_preferences(self, **kwargs) -> None:
        """Save arbitrary key-value preferences (budget, colour, etc.)."""
        self.preferences.update(kwargs)

    def summary(self) -> dict:
        """Return a snapshot of session stats for the CLI display."""
        return {
            "session_id":    self.session_id,
            "turns":         self.turn_count,
            "history_len":   len(self._history),
            "seen_products": len(self.seen_ids),
            "preferences":   self.preferences,
            "has_last_search": self.last_search_params is not None,
            "age_seconds":   round(time.time() - self.created_at, 1),
        }


# ── Global session registry ───────────────────────────────────────────────────
_sessions: dict[str, InMemorySession] = {}            # session_id → session


def get_or_create_session(session_id: str, max_history: int = 40) -> InMemorySession:
    """Fetch an existing session or create a fresh one."""
    if session_id not in _sessions:
        _sessions[session_id] = InMemorySession(session_id, max_history)
    return _sessions[session_id]


def list_sessions() -> list[str]:
    """Return all active session IDs (for debugging)."""
    return list(_sessions.keys())


def drop_session(session_id: str) -> None:
    """Delete a session from the registry."""
    _sessions.pop(session_id, None)
