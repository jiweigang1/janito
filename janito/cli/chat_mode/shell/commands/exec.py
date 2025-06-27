from janito.cli.console import shared_console
from janito.cli.chat_mode.shell.commands.base import ShellCmdHandler

class ExecShellHandler(ShellCmdHandler):
    help_text = "/exec on|off: Enable or disable code and command execution tools. Usage: /exec on or /exec off."

    def run(self):
        if not self.shell_state:
            shared_console.print("[red]Shell state unavailable.[/red]")
            return
        arg = (self.after_cmd_line or "").strip().lower()
        if arg not in ("on", "off"):
            shared_console.print("[yellow]Usage: /exec on|off[/yellow]")
            return
        enable = arg == "on"
        self.shell_state.allow_execution = enable
        # Dynamically enable/disable execution tools in the registry
        try:
            registry = __import__('janito.tools', fromlist=['get_local_tools_adapter']).get_local_tools_adapter()
            if hasattr(registry, 'set_execution_tools_enabled'):
                registry.set_execution_tools_enabled(enable)
        except Exception as e:
            shared_console.print(f"[yellow]Warning: Could not update execution tools dynamically: {e}[/yellow]")
        if enable:
            shared_console.print("[green]Execution tools ENABLED. You can now use code and command execution tools.[/green]")
        else:
            shared_console.print("[yellow]Execution tools DISABLED. Code and command execution tools are now blocked.[/yellow]")
