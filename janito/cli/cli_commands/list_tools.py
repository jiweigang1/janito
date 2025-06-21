"""
CLI Command: List available tools
"""


def handle_list_tools(args=None):
    from janito.tools.adapters.local.adapter import LocalToolsAdapter
    import janito.tools  # Ensure all tools are registered

    registry = janito.tools.get_local_tools_adapter()
    tools = registry.list_tools()
    if tools:
        from rich.table import Table
        from rich.console import Console
        console = Console()
        # Get tool instances to check provides_execution and get info
        tool_instances = {t.tool_name: t for t in registry.get_tools()}
        normal_tools = []
        exec_tools = []
        for tool in tools:
            inst = tool_instances.get(tool, None)
            # Extract parameter names from run signature
            param_names = []
            if inst and hasattr(inst, "run"):
                import inspect
                sig = inspect.signature(inst.run)
                param_names = [p for p in sig.parameters if p != "self"]
            info = {
                "name": tool,
                "params": ", ".join(param_names),
            }
            if getattr(inst, "provides_execution", False):
                exec_tools.append(info)
            else:
                normal_tools.append(info)
        table = Table(title="Registered tools", show_header=True, header_style="bold", show_lines=False, box=None)
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Parameters", style="yellow")
        for info in normal_tools:
            table.add_row(info["name"], info["params"] or "-")
        console.print(table)
        if exec_tools:
            exec_table = Table(title="Execution tools (only available with -x)", show_header=True, header_style="bold", show_lines=False, box=None)
            exec_table.add_column("Name", style="cyan", no_wrap=True)
            exec_table.add_column("Parameters", style="yellow")
            for info in exec_tools:
                exec_table.add_row(info["name"], info["params"] or "-")
            console.print(exec_table)
    else:
        print("No tools registered.")
    import sys

    sys.exit(0)
