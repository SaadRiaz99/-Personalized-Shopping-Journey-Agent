import asyncio
import sys
import pathlib
import logging
sys.path.insert(0, str(pathlib.Path(__file__).parent))
logging.getLogger().setLevel(logging.ERROR)
logging.getLogger("agents").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("openai").setLevel(logging.ERROR)

from rich.console import Console
from rich.panel   import Panel

from agent.agent          import run_turn
from agent.session_memory import drop_session
from agents               import InputGuardrailTripwireTriggered, OutputGuardrailTripwireTriggered
from openai import APIStatusError, APITimeoutError, APIConnectionError, RateLimitError

console = Console()
SESSION_ID = "cli-session"

_FRIENDLY = {
    "off_topic": "I can only help with product recommendations. Try asking about products!",
    "default":   "Let me know what product you're looking for!",
    "error":     "Something went wrong. Please try again.",
    "down":      "Service unavailable. Please try again later.",
}


async def main():
    import agent.products

    while True:
        try:
            user_input = console.input("[bold cyan]You:[/] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\nBye!")
            break

        if not user_input:
            continue

        if user_input.lower() in ("/quit", "/exit", "quit", "exit"):
            console.print("Bye!")
            break

        if user_input.lower() == "/reset":
            drop_session(SESSION_ID)
            console.print("Session cleared.")
            continue

        try:
            with console.status("[bold cyan]Thinking...[/]", spinner="dots"):
                result = await run_turn(
                    user_message=user_input,
                    session_id=SESSION_ID,
                    user_id="cli-user",
                )
            console.print(f"[bold green]Agent:[/] {result['response']}")

        except (InputGuardrailTripwireTriggered, OutputGuardrailTripwireTriggered):
            console.print(f"[yellow]Agent:[/] {_FRIENDLY['off_topic']}")

        except (APIStatusError, APITimeoutError, APIConnectionError, RateLimitError):
            console.print(f"[yellow]Agent:[/] {_FRIENDLY['down']}")

        except Exception:
            console.print(f"[yellow]Agent:[/] {_FRIENDLY['error']}")


if __name__ == "__main__":
    asyncio.run(main())
