from janito.tool_registry import ToolRegistry

class ToolExecutor:
    """
    Responsible for executing tools (functions, scripts, etc.) within the janito framework.
    Handles input, output, and error management for tool execution.
    Can integrate with ToolRegistry to resolve and execute tools by name.
    """
    def __init__(self, registry: ToolRegistry = None):
        self.registry = registry or ToolRegistry()

    def execute(self, tool, *args, **kwargs):
        """
        Execute the given tool with provided arguments.
        Args:
            tool: The tool (callable or object with an execute or run method) to run.
            *args: Positional arguments for the tool.
            **kwargs: Keyword arguments for the tool.
        Returns:
            The result of the tool execution.
        Raises:
            Exception if execution fails.
        """
        if callable(tool):
            return tool(*args, **kwargs)
        elif hasattr(tool, 'execute') and callable(getattr(tool, 'execute')):
            return tool.execute(*args, **kwargs)
        elif hasattr(tool, 'run') and callable(getattr(tool, 'run')):
            return tool.run(*args, **kwargs)
        else:
            raise ValueError("Provided tool is not executable.")

    def execute_by_name(self, tool_name: str, *args, **kwargs):
        """
        Execute a registered tool by its name using the ToolRegistry.
        Args:
            tool_name: The name of the registered tool.
            *args: Positional arguments for the tool.
            **kwargs: Keyword arguments for the tool.
        Returns:
            The result of the tool execution.
        Raises:
            Exception if tool is not found or execution fails.
        """
        tool = self.registry.get_tool(tool_name)
        if tool is None:
            raise ValueError(f"Tool '{tool_name}' not found in registry.")
        return self.execute(tool, *args, **kwargs)
