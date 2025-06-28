"""
CLI Command: List available tools
"""


def handle_list_tools(args=None):
    from janito.tools.adapters.local.adapter import LocalToolsAdapter
    import janito.tools  # Ensure all tools are registered

    # Determine permissions from args (default: all False)
    from janito.tools.tool_base import ToolPermissions
    read = getattr(args, "read", False) if args else False
    write = getattr(args, "write", False) if args else False
    execute = getattr(args, "exec", False) if args else False
    # If no permissions are specified, assume user wants to list all tools
    if not (read or write or execute):
        read = write = execute = True
    from janito.tools.permissions import set_global_allowed_permissions
    set_global_allowed_permissions(ToolPermissions(read=read, write=write, execute=execute))
    registry = janito.tools.get_local_tools_adapter()
    tools = registry.list_tools()
    if tools:
        from rich.table import Table
        from rich.console import Console
        console = Console()
        # Get tool instances to check provides_execution and get info
        tool_instances = {t.tool_name: t for t in registry.get_tools()}
        read_only_tools = []
        write_only_tools = []
        read_write_tools = []
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
            perms = getattr(inst, "permissions", None)
            if perms and perms.execute:
                exec_tools.append(info)
            elif perms and perms.read and perms.write:
                read_write_tools.append(info)
            elif perms and perms.read:
                read_only_tools.append(info)
            elif perms and perms.write:
                write_only_tools.append(info)
        # Print each group if not empty
        if read_only_tools:
            table = Table(title="Read-only tools (-r)", show_header=True, header_style="bold", show_lines=False, box=None)
            table.add_column("Name", style="cyan", no_wrap=True)
            table.add_column("Parameters", style="yellow")
            for info in read_only_tools:
                table.add_row(info["name"], info["params"] or "-")
            console.print(table)
        if write_only_tools:
            table = Table(title="Write-only tools (-w)", show_header=True, header_style="bold", show_lines=False, box=None)
            table.add_column("Name", style="cyan", no_wrap=True)
            table.add_column("Parameters", style="yellow")
            for info in write_only_tools:
                table.add_row(info["name"], info["params"] or "-")
            console.print(table)
        if read_write_tools:
            table = Table(title="Read-Write tools (-rw)", show_header=True, header_style="bold", show_lines=False, box=None)
            table.add_column("Name", style="cyan", no_wrap=True)
            table.add_column("Parameters", style="yellow")
            for info in read_write_tools:
                table.add_row(info["name"], info["params"] or "-")
            console.print(table)
        if exec_tools:
            exec_table = Table(title="Execution tools (-x)", show_header=True, header_style="bold", show_lines=False, box=None)
            exec_table.add_column("Name", style="cyan", no_wrap=True)
            exec_table.add_column("Parameters", style="yellow")
            for info in exec_tools:
                exec_table.add_row(info["name"], info["params"] or "-")
            console.print(exec_table)
    else:
        print("No tools registered.")
    import sys

    sys.exit(0)
