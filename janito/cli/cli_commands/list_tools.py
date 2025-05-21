"""
CLI Command: List available tools
"""

def handle_list_tools(args=None):
    from janito.tool_registry import ToolRegistry
    import janito.tools  # Ensure all tools are registered
    registry = ToolRegistry()
    tools = registry.list_tools()
    if tools:
        print("Registered tools:")
        for tool in tools:
            print(f"- {tool}")
    else:
        print("No tools registered.")
    import sys
    sys.exit(0)
