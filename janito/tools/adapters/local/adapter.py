from typing import Type, Dict, Any
from janito.tools.tools_adapter import ToolsAdapterBase as ToolsAdapter


class LocalToolsAdapter(ToolsAdapter):
    """Local, in-process implementation of :class:`ToolsAdapterBase`.

    This adapter keeps an **in-memory registry** of tool classes and manages
    permission filtering (read/write/execute) as required by the janito CLI.

    The legacy ``set_execution_tools_enabled()`` helper has been removed – use
    ``janito.tools.permissions.set_global_allowed_permissions`` or
    :py:meth:`LocalToolsAdapter.set_allowed_permissions` to adjust the
    permission mask at runtime.

    Apart from registration/lookup helpers the class derives all execution
    logic from :class:`janito.tools.tools_adapter.ToolsAdapterBase`.
    """

    def __init__(self, tools=None, event_bus=None, workdir=None):
        super().__init__(tools=tools, event_bus=event_bus)
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
        return [name for name, entry in self._tools.items() if self.is_tool_allowed(entry["instance"])]

    def get_tool_classes(self):
        return [entry["class"] for entry in self._tools.values() if self.is_tool_allowed(entry["instance"])]

    def get_tools(self):
        return [entry["instance"] for entry in self._tools.values() if self.is_tool_allowed(entry["instance"])]


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
        from janito.tools.tool_base import ToolPermissions
        from janito.tools.permissions import get_global_allowed_permissions
        LocalToolsAdapter().register_tool(cls)
        return cls

    if tool is None:
        return decorator
    return decorator(tool)

