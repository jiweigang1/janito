from janito.tool_registry import ToolRegistry
from janito.event_bus.bus import event_bus as default_event_bus
from janito.tool_events import ToolCallStarted, ToolCallFinished
from janito.tool_base import ToolBase

class ToolExecutor:
    """
    Responsible for executing tools (functions, scripts, etc.) within the janito framework.
    Handles input, output, and error management for tool execution.
    Integrates with ToolRegistry to resolve and execute tools by name.
    Emits events for tool execution lifecycle using the event_bus (can be overridden per instance).
    """
    def __init__(self, registry: ToolRegistry = None, event_bus=None):
        self.registry = registry or ToolRegistry()
        self._event_bus = event_bus or default_event_bus

    @property
    def event_bus(self):
        return self._event_bus

    @event_bus.setter
    def event_bus(self, bus):
        self._event_bus = bus or default_event_bus

    def execute(self, tool, *args, **kwargs):
        # If the tool is a ToolBase instance, propagate the event bus
        if isinstance(tool, ToolBase):
            tool.event_bus = self._event_bus
        if callable(tool):
            return tool(*args, **kwargs)
        elif hasattr(tool, 'execute') and callable(getattr(tool, 'execute')):
            return tool.execute(*args, **kwargs)
        elif hasattr(tool, 'run') and callable(getattr(tool, 'run')):
            return tool.run(*args, **kwargs)
        else:
            raise ValueError("Provided tool is not executable.")

    def execute_by_name(self, tool_name: str, *args, request_id=None, arguments=None, **kwargs):
        tool = self.registry.get_tool(tool_name)
        if tool is None:
            raise ValueError(f"Tool '{tool_name}' not found in registry.")
        self._event_bus.publish(ToolCallStarted(tool_name=tool_name, request_id=request_id, arguments=arguments))
        result = self.execute(tool, *(arguments or []), **kwargs)
        self._event_bus.publish(ToolCallFinished(tool_name=tool_name, request_id=request_id, result=result))
        return result
