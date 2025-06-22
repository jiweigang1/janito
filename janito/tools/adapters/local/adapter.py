from typing import Type, Dict, Any
from janito.tools.tools_adapter import ToolsAdapterBase as ToolsAdapter


class LocalToolsAdapter(ToolsAdapter):
    def disable_execution_tools(self):
        """Unregister all tools with provides_execution = True."""
        to_remove = [name for name, entry in self._tools.items()
                     if getattr(entry["instance"], "provides_execution", False)]
        for name in to_remove:
            self.unregister_tool(name)

    """
    Adapter for local, statically registered tools in the agent/tools system.
    Handles registration, lookup, enabling/disabling, listing, and now, tool execution (merged from executor).
    """

    def __init__(self, tools=None, event_bus=None, allowed_tools=None, workdir=None):
        super().__init__(tools=tools, event_bus=event_bus, allowed_tools=allowed_tools)
        self._tools: Dict[str, Dict[str, Any]] = {}
        self.workdir = workdir
        if self.workdir:
            import os
            os.chdir(self.workdir)
        if tools:
            for tool in tools:
                self.register_tool(tool)

    def register_tool(self, tool_class: Type):
        instance = tool_class()
        if not hasattr(instance, "run") or not callable(instance.run):
            raise TypeError(
                f"Tool '{tool_class.__name__}' must implement a callable 'run' method."
            )
        tool_name = getattr(instance, "tool_name", None)
        if not tool_name or not isinstance(tool_name, str):
            raise ValueError(
                f"Tool '{tool_class.__name__}' must provide a class attribute 'tool_name' (str) for its registration name."
            )
        if tool_name in self._tools:
            raise ValueError(f"Tool '{tool_name}' is already registered.")
        self._tools[tool_name] = {
            "function": instance.run,
            "class": tool_class,
            "instance": instance,
        }

    def unregister_tool(self, name: str):
        if name in self._tools:
            del self._tools[name]

    def disable_tool(self, name: str):
        self.unregister_tool(name)

    def get_tool(self, name: str):
        return self._tools[name]["instance"] if name in self._tools else None

    def list_tools(self):
        return list(self._tools.keys())

    def get_tool_classes(self):
        return [entry["class"] for entry in self._tools.values()]

    def get_tools(self):
        return [entry["instance"] for entry in self._tools.values()]


    def add_tool(self, tool):
        # Register by instance (useful for hand-built objects)
        if not hasattr(tool, "run") or not callable(tool.run):
            raise TypeError(f"Tool '{tool}' must implement a callable 'run' method.")
        tool_name = getattr(tool, "tool_name", None)
        if not tool_name or not isinstance(tool_name, str):
            raise ValueError(
                f"Tool '{tool}' must provide a 'tool_name' (str) attribute."
            )
        if tool_name in self._tools:
            raise ValueError(f"Tool '{tool_name}' is already registered.")
        self._tools[tool_name] = {
            "function": tool.run,
            "class": tool.__class__,
            "instance": tool,
        }


# Optional: a local-tool decorator


def register_local_tool(tool=None):
    def decorator(cls):
        LocalToolsAdapter().register_tool(cls)
        return cls

    if tool is None:
        return decorator
    return decorator(tool)
