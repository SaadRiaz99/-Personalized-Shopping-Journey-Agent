"""
context.py
----------
AgentContext — a data class threaded through RunContextWrapper
so that every @function_tool can access the current session, user info,
and tool-call log via `ctx.context`.
"""

from __future__ import annotations
from dataclasses import dataclass, field              # Lightweight data container
from .session_memory import InMemorySession           # Session for this conversation


@dataclass
class AgentContext:
    """
    Per-request context injected into every tool call.

    Fields
    ------
    session       : the live InMemorySession (history, seen products, preferences)
    user_id       : caller identity (for logging / personalisation)
    request_id    : unique ID for this Runner.run() call
    tool_call_log : list of [tool_name] summary strings accumulated this turn
    """
    session:       InMemorySession                   # Session with history + metadata
    user_id:       str             = "anonymous"      # Default if not provided
    request_id:    str             = ""               # Set per-run_turn() call
    tool_call_log: list[str]       = field(default_factory=list)  # Auto-initialised list

    def log_tool(self, tool_name: str, summary: str) -> None:
        """Record a tool call so it can be returned to the CLI."""
        entry = f"[{tool_name}] {summary}"
        self.tool_call_log.append(entry)

    def get_context_summary(self) -> dict:
        """Return a dict summarising the current context (for debugging)."""
        return {
            "user_id":      self.user_id,
            "request_id":   self.request_id,
            "session":      self.session.summary(),
            "tools_called": self.tool_call_log,
        }
