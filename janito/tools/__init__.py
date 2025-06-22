from janito.tools.adapters.local import (
    local_tools_adapter as _internal_local_tools_adapter,
    LocalToolsAdapter,
)


def get_local_tools_adapter(workdir=None):
    # Use set_verbose_tools on the returned adapter to set verbosity as needed
    if workdir is not None:
        import os
        if not os.path.exists(workdir):
            os.makedirs(workdir, exist_ok=True)
        return LocalToolsAdapter(workdir=workdir)
    return _internal_local_tools_adapter


__all__ = [
    "LocalToolsAdapter",
    "get_local_tools_adapter",
]
