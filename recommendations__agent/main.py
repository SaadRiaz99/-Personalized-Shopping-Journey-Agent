"""
main.py
-------
Interactive CLI for chatting with ShopBot.
Run:  python main.py
"""

import asyncio                              # Async runtime
import sys                                  # sys.path manipulation
import pathlib                              # Parent-directory resolution
sys.path.insert(0, str(pathlib.Path(__file__).parent))  # Add project root to import path

from rich.console import Console             # Coloured terminal output
from rich.panel   import Panel               # Bordered text boxes
from rich.text    import Text                # Styled text fragments
from rich.table   import Table               # Tabular data display
from rich         import print as rprint     # Rich-enhanced print

from agent.agent          import run_turn    # Main agent entry point
from agent.session_memory import drop_session  # Session reset
from agents               import InputGuardrailTripwireTriggered, OutputGuardrailTripwireTriggered

console = Console()
SESSION_ID = "cli-session"                   # Fixed session key for CLI user


def print_header():
    """Display the startup banner."""
    console.print(Panel.fit(
        "[bold cyan]ShopBot[/] - AI-Powered Product Recommendation Agent\n"
        "[dim]Powered by Gemini 2.5 Flash . OpenAI Agents SDK . 1M product catalogue[/]",
        border_style="cyan"
    ))
    console.print("[dim]Commands:  /quit | /reset (clear session) | /session (show stats)[/]\n")


def print_response(result: dict):
    """Print the agent reply, tool calls, and session stats."""
    # Agent text response
    console.print(Panel(
        result["response"],
        title="[bold green]ShopBot[/]",
        border_style="green",
    ))

    # Tool call log for this turn
    if result["tool_calls"]:
        console.print("[dim]Tools called this turn:[/]")
        for entry in result["tool_calls"]:
            console.print(f"  [dim cyan]{entry}[/]")

    # Compact session summary line
    s = result["session_summary"]
    console.print(
        f"[dim]  Session: turn {s['turns']} | {s['seen_products']} products seen | "
        f"history {s['history_len']} items[/]\n"
    )


async def main():
    """CLI event loop: read input, call agent, display output."""
    print_header()
    console.print("[yellow]Loading 1M-product catalogue...[/]")

    import agent.products                     # Trigger JSON load so the file is validated early

    console.print("[green]Ready![/]\n")

    while True:
        try:
            user_input = console.input("[bold cyan]You:[/] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Bye![/]")
            break

        if not user_input:
            continue

        # ── Built-in commands ────────────────────────────────────────────────
        if user_input.lower() in ("/quit", "/exit", "quit", "exit"):
            console.print("[dim]Bye![/]")
            break

        if user_input.lower() == "/reset":
            drop_session(SESSION_ID)
            console.print("[yellow]Session cleared.[/]\n")
            continue

        if user_input.lower() == "/session":
            from agent.session_memory import get_or_create_session
            s = get_or_create_session(SESSION_ID).summary()
            rprint(s)
            continue

        # ── Normal message → agent ───────────────────────────────────────────
        try:
            result = await run_turn(
                user_message=user_input,
                session_id=SESSION_ID,
                user_id="cli-user",
            )
            print_response(result)

        except InputGuardrailTripwireTriggered as e:
            console.print(Panel(
                f"[red]Input blocked by guardrail.[/]\n{e}",
                title="[bold red]Guardrail triggered[/]",
                border_style="red",
            ))

        except OutputGuardrailTripwireTriggered as e:
            console.print(Panel(
                f"[red]Response blocked by output guardrail.[/]\n{e}",
                title="[bold red]Output guardrail triggered[/]",
                border_style="red",
            ))

        except Exception as e:
            console.print(f"[bold red]Error:[/] {e}")


if __name__ == "__main__":
    asyncio.run(main())
