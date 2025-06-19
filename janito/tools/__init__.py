from janito.tools.adapters.local import (
    local_tools_adapter as _internal_local_tools_adapter,
    LocalToolsAdapter,
)


def get_local_tools_adapter():

    # Use set_verbose_tools on the returned adapter to set verbosity as needed
    return _internal_local_tools_adapter


__all__ = [
    "LocalToolsAdapter",
    "get_local_tools_adapter",
]
