class ToolsAdapterBase:
    """
    Composable entry point for tools management and provisioning in LLM pipelines.
    This class represents an external or plugin-based provider of tool definitions.
    Extend and customize this to load, register, or serve tool implementations dynamically.
    """
    def __init__(self, tools=None):
        self._tools = tools or []

    def get_tools(self):
        """Return the list of tools managed by this provider."""
        return self._tools

    def add_tool(self, tool):
        self._tools.append(tool)

    def clear_tools(self):
        self._tools = []
