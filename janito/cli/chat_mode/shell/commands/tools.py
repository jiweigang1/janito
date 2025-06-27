from janito.cli.console import shared_console
from janito.cli.chat_mode.shell.commands.base import ShellCmdHandler

class ToolsShellHandler(ShellCmdHandler):
    help_text = "List available tools"

    def run(self):
        try:
            # Initialize allow_execution before use
            allow_execution = False
            if hasattr(self, 'shell_state') and self.shell_state is not None:
                allow_execution = getattr(self.shell_state, 'allow_execution', False)

            import janito.tools  # Ensure all tools are registered
            registry = janito.tools.get_local_tools_adapter()
            tools = registry.list_tools()
            shared_console.print("Registered tools:" if tools else "No tools registered.")
            # Get tool instances for annotation
            tool_instances = {t.tool_name: t for t in registry.get_tools()}
            for tool in tools:
                inst = tool_instances.get(tool, None)
                is_exec = getattr(inst, 'provides_execution', False) if inst else False
                if is_exec and not allow_execution:
                    shared_console.print(f"- {tool} (disabled)")
                else:
                    shared_console.print(f"- {tool}")

            if allow_execution:
                shared_console.print("[green]Execution tools are ENABLED.[/green]")
            else:
                shared_console.print("[yellow]Execution tools are DISABLED. Use /exec on to enable them.[/yellow]")

            # Find all possible execution tools (by convention: provides_execution = True)
            exec_tools = []
            for tool_instance in registry.get_tools():
                if getattr(tool_instance, 'provides_execution', False):
                    exec_tools.append(tool_instance.tool_name)

            if not allow_execution and exec_tools:
                shared_console.print("[yellow]⚠️  Warning: Execution tools (e.g., commands, code execution) are disabled. Use -x to enable them.[/yellow]")

        except Exception as e:
            shared_console.print(f"[red]Error loading tools: {e}[/red]")
