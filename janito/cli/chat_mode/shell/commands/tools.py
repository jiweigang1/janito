from janito.tools.adapters.local.adapter import LocalToolsAdapter
from rich.table import Table

from janito.cli.console import shared_console

from janito.tools.adapters.local.adapter import LocalToolsAdapter
from rich.table import Table
from janito.cli.console import shared_console
from janito.cli.chat_mode.shell.commands.base import ShellCmdHandler

class ToolsShellHandler(ShellCmdHandler):
    help_text = "List available tools"

    def run(self):
        table = Table(title="Available Tools", show_lines=True, style="bold magenta")
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Description", style="green")
        table.add_column("Parameters", style="yellow")
        try:
            registry = LocalToolsAdapter()
            for tool_class in registry.get_tool_classes():
                instance = tool_class()
                fn = getattr(instance, 'run', None)
                name = getattr(instance, 'name', tool_class.__name__)
                description = getattr(instance, 'description', fn.__doc__ if fn else '') or '-'
                params = "\n".join([
                    f"[bold]{k}[/]: {v}" for k, v in getattr(instance, 'parameters', {}).items()
                ]) if hasattr(instance, 'parameters') else "-"
                table.add_row(f"[b]{name}[/b]", description, params)
        except Exception as e:
            shared_console.print(f"[red]Error loading tools: {e}[/red]")
            return
        shared_console.print(table)
