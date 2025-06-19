from janito.cli.chat_mode.shell.commands.base import ShellCmdHandler
from janito.cli.console import shared_console


class HelpShellHandler(ShellCmdHandler):
    help_text = "Show this help message"

    def run(self):
        from . import (
            COMMAND_HANDLERS,
        )  # Import moved inside method to avoid circular import

        shared_console.print("[bold magenta]Available commands:[/bold magenta]")
        for cmd, handler_cls in sorted(COMMAND_HANDLERS.items()):
            help_text = getattr(handler_cls, "help_text", "")
            shared_console.print(f"[cyan]{cmd}[/cyan]: {help_text}")
