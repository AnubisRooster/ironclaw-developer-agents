"""Interactive CLI chat interface for the developer automation agent."""

from __future__ import annotations

import asyncio
import logging

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.theme import Theme

logger = logging.getLogger("claw-agent.cli")

custom_theme = Theme(
    {
        "info": "cyan",
        "warning": "yellow",
        "error": "bold red",
        "agent": "bold green",
        "user": "bold blue",
    }
)
console = Console(theme=custom_theme)


def _print_banner() -> None:
    console.print(
        Panel.fit(
            "[bold cyan]Claw Agent[/bold cyan] — Developer Automation Assistant\n"
            "Type your request in natural language. Type [bold]/quit[/bold] to exit.",
            border_style="cyan",
        )
    )


async def _chat_loop(orchestrator) -> None:  # noqa: ANN001
    """Run the interactive prompt loop."""
    _print_banner()

    while True:
        try:
            user_input = console.input("\n[user]You >[/user] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[info]Goodbye.[/info]")
            break

        if not user_input:
            continue
        if user_input.lower() in ("/quit", "/exit", "quit", "exit"):
            console.print("[info]Goodbye.[/info]")
            break

        with console.status("[info]Thinking...[/info]", spinner="dots"):
            try:
                response = await orchestrator.handle_message(user_input)
            except Exception as exc:
                logger.exception("Error handling message")
                console.print(f"[error]Error: {exc}[/error]")
                continue

        console.print()
        console.print(Panel(Markdown(response), title="[agent]Claw Agent[/agent]", border_style="green"))


def start_chat(orchestrator) -> None:  # noqa: ANN001
    """Entry point called from main.py for the 'chat' command."""
    asyncio.run(_chat_loop(orchestrator))
