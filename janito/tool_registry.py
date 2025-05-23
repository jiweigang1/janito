from typing import Type, Dict, Any

def get_tool_schemas():
    """Return schemas for all registered tools using the OpenAI schema generator."""
    from janito.providers.openai.schema_generator import generate_tool_schemas
    return generate_tool_schemas(ToolRegistry().get_tool_classes())

class ToolRegistry:
    _instance = None
    _tools: Dict[str, Dict[str, Any]] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def register_tool(self, tool_class: Type):
        instance = tool_class()
        if not hasattr(instance, "run") or not callable(instance.run):
            raise TypeError(f"Tool '{tool_class.__name__}' must implement a callable 'run' method.")
        tool_name = getattr(instance, 'name', None)
        if not tool_name or not isinstance(tool_name, str):
            raise ValueError(f"Tool '{tool_class.__name__}' must provide a class attribute 'name' (str) for its registration name.")
        tool_class._tool_run_method = instance.run
        tool_class._tool_name = tool_name
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
        """
        Mark the tool as disabled (remove from registry but keep as a known tool)."""
        self.unregister_tool(name)

    def get_tool(self, name: str):
        return self._tools[name]["instance"] if name in self._tools else None

    def list_tools(self):
        return list(self._tools.keys())

    def get_tool_classes(self):
        return [entry["class"] for entry in self._tools.values()]

def register_tool(tool=None):
    def decorator(cls):
        ToolRegistry().register_tool(cls)
        return cls
    if tool is None:
        return decorator
    return decorator(tool)
