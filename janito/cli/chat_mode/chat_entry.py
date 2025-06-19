"""
Main entry point for the Janito Chat CLI.
Handles the interactive chat loop and session startup.
"""

from rich.console import Console
from prompt_toolkit.formatted_text import HTML
from janito.cli.chat_mode.session import ChatSession


def main(args=None):
    console = Console()
    from janito.version import __version__

    console.print(
        f"[bold green]Welcome to the Janito Chat Mode (v{__version__})! Type /exit or press Ctrl+C to quit.[/bold green]"
    )
    session = ChatSession(console, args=args)
    session.run()


if __name__ == "__main__":
    main()
