"""CLI entry point for the multi-model comparison agent."""
import argparse
import asyncio

from rich.columns import Columns
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from .agent import budget_agent, quality_agent, run_comparison

console = Console()


async def single_prompt(prompt: str) -> None:
    with console.status("[dim]Running comparison...[/dim]"):
        results = await run_comparison(prompt)

    budget_panel = Panel(
        Markdown(results["budget"]),
        title="[bold green]BudgetFinder[/bold green]",
        border_style="green",
    )
    quality_panel = Panel(
        Markdown(results["quality"]),
        title="[bold blue]QualityFinder[/bold blue]",
        border_style="blue",
    )
    console.print(Columns([budget_panel, quality_panel], equal=True))


async def interactive() -> None:
    console.print("[bold]Multi-Model Comparison Agent[/bold] — type your query or [dim]/quit[/dim]")
    console.print("  [green]BudgetFinder[/green] focuses on value · [blue]QualityFinder[/blue] focuses on premium")
    while True:
        prompt = console.input("\n[bold]>[/bold] ")
        if prompt.strip().lower() in ("/quit", "/exit", ""):
            break
        await single_prompt(prompt)


def main() -> None:
    if budget_agent is None and quality_agent is None:
        console.print("[red]No API key found. Set GROQ_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY, or OPENROUTER_API_KEY.[/red]")
        return

    parser = argparse.ArgumentParser(description="Multi-model comparison agent")
    parser.add_argument("prompt", nargs="?", help="One-shot comparison query")
    parser.add_argument("-i", "--interactive", action="store_true", help="Interactive REPL mode")
    args = parser.parse_args()

    if args.interactive or not args.prompt:
        asyncio.run(interactive())
    else:
        asyncio.run(single_prompt(args.prompt))


if __name__ == "__main__":
    main()
