from janito.cli.console import shared_console
from janito.cli.chat_mode.shell.commands.base import ShellCmdHandler

class ToolsShellHandler(ShellCmdHandler):
    help_text = "List available tools"

    def run(self):
        try:
            import janito.tools  # Ensure all tools are registered
            registry = janito.tools.get_local_tools_adapter()
            tools = registry.list_tools()
            shared_console.print("Registered tools:" if tools else "No tools registered.")
            for tool in tools:
                shared_console.print(f"- {tool}")

            # Check for execution tools
            # We assume shell_state.allow_execution is set if -x is used
            allow_execution = False
            if hasattr(self, 'shell_state') and self.shell_state is not None:
                allow_execution = getattr(self.shell_state, 'allow_execution', False)

            # Find all possible execution tools (by convention: provides_execution = True)
            exec_tools = []
            for tool_instance in registry.get_tools():
                if getattr(tool_instance, 'provides_execution', False):
                    exec_tools.append(tool_instance.tool_name)

            if not allow_execution and exec_tools:
                shared_console.print("[yellow]⚠️  Warning: Execution tools (e.g., commands, code execution) are disabled. Use -x to enable them.[/yellow]")

        except Exception as e:
            shared_console.print(f"[red]Error loading tools: {e}[/red]")
