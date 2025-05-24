from janito.tools.adapters.local import local_tools_adapter as _internal_local_tools_adapter

# Optionally provide a helper to access tools
get_local_tools_adapter = lambda: _internal_local_tools_adapter

__all__ = [
    "LocalToolsAdapter",
    "get_local_tools_adapter",
]
