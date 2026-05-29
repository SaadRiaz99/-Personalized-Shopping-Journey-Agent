"""
tracing.py
----------
Custom TracingProcessor that:
1. Pretty-prints every span to the console (via rich if available).
2. Appends every completed span as a JSONL line to traces.jsonl.
3. Forwards traces to the OpenAI tracing dashboard (key set in config.py).

Registered automatically when this module is imported (see bottom of file).
"""

from __future__ import annotations
import json                                    # For JSONL logging
import time                                    # For elapsed-time measurement
import pathlib                                 # File path for traces.jsonl
from agents import TracingProcessor, Trace, Span, add_trace_processor

# Optional rich dependency for coloured console output
try:
    from rich.console import Console
    from rich.text import Text
    _console = Console()
    _RICH = True
except ImportError:
    _RICH = False

_LOG_PATH = pathlib.Path("traces.jsonl")       # Where span records are saved


class RecommendationTracingProcessor(TracingProcessor):
    """
    Logs every trace/span to the console (via rich) and to traces.jsonl.
    Instantiated and registered at module import time.
    """

    def __init__(self, log_path: pathlib.Path = _LOG_PATH, verbose: bool = False):
        self._log_path = log_path
        self._verbose  = verbose               # Show start events too (off by default)
        self._active_traces: dict[str, float] = {}   # trace_id → start_time

    # ── Trace lifecycle ───────────────────────────────────────────────────────
    def on_trace_start(self, trace: Trace) -> None:
        """Record the start time of a trace (for elapsed calculation)."""
        self._active_traces[trace.trace_id] = time.time()
        if self._verbose:
            self._print(f"[TRACE START] [{trace.trace_id[:8]}]  {trace.name}", style="bold cyan")

    def on_trace_end(self, trace: Trace) -> None:
        """Log end of trace with elapsed time."""
        start = self._active_traces.pop(trace.trace_id, time.time())
        elapsed = round(time.time() - start, 3)
        self._print(
            f"[TRACE END]   [{trace.trace_id[:8]}]  {trace.name}  ({elapsed}s)",
            style="bold green",
        )
        self._write_jsonl({
            "event":    "trace_end",
            "trace_id": trace.trace_id,
            "name":     trace.name,
            "elapsed":  elapsed,
        })

    # ── Span lifecycle ────────────────────────────────────────────────────────
    def on_span_start(self, span: Span) -> None:
        """Log start of a span (only in verbose mode)."""
        if self._verbose:
            self._print(
                f"  [SPAN START] [{span.span_id[:8]}]  {self._span_label(span)}",
                style="dim",
            )

    def on_span_end(self, span: Span) -> None:
        """Log end of span with optional error marker."""
        label   = self._span_label(span)
        error   = getattr(span, "error", None)
        style   = "red" if error else "green"
        suffix  = f"  [ERR] {error}" if error else ""

        self._print(f"  [OK] SPAN END  [{span.span_id[:8]}]  {label}{suffix}", style=style)
        self._write_jsonl({
            "event":    "span_end",
            "span_id":  span.span_id,
            "trace_id": span.trace_id,
            "label":    label,
            "error":    str(error) if error else None,
        })

    # ── Cleanup ───────────────────────────────────────────────────────────────
    def shutdown(self) -> None:
        """Clear trace timestamps on shutdown."""
        self._active_traces.clear()

    def force_flush(self) -> None:
        """No-op — we write synchronously on every event."""
        pass

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _span_label(self, span: Span) -> str:
        """Build a human-readable label for a span (e.g. 'AgentSpanData:ShopBot')."""
        data = getattr(span, "span_data", None)
        if data is None:
            return "span"
        kind = type(data).__name__
        name = getattr(data, "name", "") or getattr(data, "tool_name", "") or ""
        return f"{kind}:{name}" if name else kind

    def _print(self, msg: str, style: str = "") -> None:
        """Print a message to the console (via rich or plain print)."""
        if _RICH:
            _console.print(Text(msg, style=style))
        else:
            try:
                print(msg)
            except UnicodeEncodeError:             # Handle Windows cp1252 console
                print(msg.encode("ascii", errors="replace").decode("ascii"))

    def _write_jsonl(self, record: dict) -> None:
        """Append a JSON line to traces.jsonl (best-effort, never crashes)."""
        try:
            with self._log_path.open("a") as f:
                f.write(json.dumps(record) + "\n")
        except Exception:
            pass                                   # Silently ignore write errors


# ── Register at module import ─────────────────────────────────────────────────
_processor = RecommendationTracingProcessor(verbose=False)
add_trace_processor(_processor)
