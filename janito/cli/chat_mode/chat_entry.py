"""
Main entry point for the Janito Chat CLI.
Handles the interactive chat loop and session startup.
"""
from rich.console import Console
from prompt_toolkit.formatted_text import HTML
from janito.cli.chat_mode.session import ChatSession

def main():
    console = Console()
    console.print("[bold green]Welcome to the Janito Chat Mode! Type /exit or press Ctrl+C to quit.[/bold green]")
    session = ChatSession(console)
    session.run()

if __name__ == "__main__":
    main()
