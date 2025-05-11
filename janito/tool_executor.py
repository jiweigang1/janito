from janito.tool_registry import ToolRegistry
from janito.event_bus.bus import event_bus
from janito.tool_events import ToolCallStarted, ToolCallFinished

class ToolExecutor:
    """
    Responsible for executing tools (functions, scripts, etc.) within the janito framework.
    Handles input, output, and error management for tool execution.
    Integrates with ToolRegistry to resolve and execute tools by name.
    Emits events for tool execution lifecycle using the global event_bus.
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

    def execute_by_name(self, tool_name: str, *args, request_id=None, arguments=None, **kwargs):
        """
        Execute a registered tool by its name using the ToolRegistry.
        Emits ToolCallStarted and ToolCallFinished events.
        Args:
            tool_name: The name of the registered tool.
            request_id: Correlation ID for the request (for event tracking).
            arguments: Arguments passed to the tool (for event context).
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
        event_bus.publish(ToolCallStarted(tool_name=tool_name, request_id=request_id, arguments=arguments))
        result = self.execute(tool, *(arguments or []), **kwargs)
        event_bus.publish(ToolCallFinished(tool_name=tool_name, request_id=request_id, result=result))
        return result
