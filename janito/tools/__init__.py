from janito.tools.adapters.local.adapter import LocalToolsAdapter

# Initialize the local adapter registry for tools
local_tools_adapter = LocalToolsAdapter()

# Optionally provide a helper to access tools
get_local_tools_adapter = lambda: local_tools_adapter

__all__ = [
    "LocalToolsAdapter",
    "local_tools_adapter",
    "get_local_tools_adapter",
]
