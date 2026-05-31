"""CLI entry point for the product recommendation agent."""
import argparse
import asyncio

from rich.console import Console
from rich.markdown import Markdown

from .agent import recommendation_agent, run_recommendation

console = Console()


async def single_prompt(prompt: str) -> None:
    console.print(f"[bold]You:[/bold] {prompt}")
    with console.status("[dim]Thinking...[/dim]"):
        response = await run_recommendation(prompt)
    console.print(Markdown(response))


async def interactive() -> None:
    console.print("[bold]Recommendation Agent[/bold] — type your query or [dim]/quit[/dim]")
    while True:
        prompt = console.input("\n[bold]>[/bold] ")
        if prompt.strip().lower() in ("/quit", "/exit", ""):
            break
        await single_prompt(prompt)


def main() -> None:
    if recommendation_agent is None:
        console.print("[red]No API key found. Set GROQ_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY, or OPENROUTER_API_KEY.[/red]")
        return

    parser = argparse.ArgumentParser(description="Product recommendation agent")
    parser.add_argument("prompt", nargs="?", help="One-shot recommendation query")
    parser.add_argument("-i", "--interactive", action="store_true", help="Interactive REPL mode")
    args = parser.parse_args()

    if args.interactive or not args.prompt:
        asyncio.run(interactive())
    else:
        asyncio.run(single_prompt(args.prompt))


if __name__ == "__main__":
    main()
