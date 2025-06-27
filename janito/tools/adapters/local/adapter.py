from typing import Type, Dict, Any
from janito.tools.tools_adapter import ToolsAdapterBase as ToolsAdapter


class LocalToolsAdapter(ToolsAdapter):
    def set_execution_tools_enabled(self, enabled: bool):
        """
        Dynamically include or exclude execution tools from the enabled_tools set.
        If enabled_tools is None, all tools are enabled (default). If set, restricts enabled tools.
        """
        all_tool_names = set(self._tools.keys())
        exec_tool_names = {
            name for name, entry in self._tools.items()
            if getattr(entry["instance"], "provides_execution", False)
        }
        if self._enabled_tools is None:
            # If not restricted, create a new enabled-tools set excluding execution tools if disabling
            if enabled:
                self._enabled_tools = None  # all tools enabled
            else:
                self._enabled_tools = all_tool_names - exec_tool_names
        else:
            if enabled:
                self._enabled_tools |= exec_tool_names
            else:
                self._enabled_tools -= exec_tool_names

    """
    Adapter for local, statically registered tools in the agent/tools system.
    Handles registration, lookup, enabling/disabling, listing, and now, tool execution (merged from executor).
    """

    def __init__(self, tools=None, event_bus=None, enabled_tools=None, workdir=None):
        super().__init__(tools=tools, event_bus=event_bus, enabled_tools=enabled_tools)
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
        if self._enabled_tools is None:
            return list(self._tools.keys())
        return [name for name in self._tools.keys() if name in self._enabled_tools]

    def get_tool_classes(self):
        if self._enabled_tools is None:
            return [entry["class"] for entry in self._tools.values()]
        return [entry["class"] for name, entry in self._tools.items() if name in self._enabled_tools]

    def get_tools(self):
        if self._enabled_tools is None:
            return [entry["instance"] for entry in self._tools.values()]
        return [entry["instance"] for name, entry in self._tools.items() if name in self._enabled_tools]


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

