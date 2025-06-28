from janito.tools.adapters.local import (
    local_tools_adapter as _internal_local_tools_adapter,
    LocalToolsAdapter,
)


def get_local_tools_adapter(workdir=None, allowed_permissions=None):
    # Use set_verbose_tools on the returned adapter to set verbosity as needed
    import os
    if workdir is not None and not os.path.exists(workdir):
        os.makedirs(workdir, exist_ok=True)
    from janito.tools.permissions import get_global_allowed_permissions
    from janito.tools.tool_base import ToolPermissions
    # Determine permissions: prefer explicitly provided, then global, then default (all False)
    if allowed_permissions is None:
        allowed_permissions = get_global_allowed_permissions()
    if allowed_permissions is None:
        allowed_permissions = ToolPermissions(read=False, write=False, execute=False)

    # Reuse the singleton adapter defined in janito.tools.adapters.local to maintain tool registrations
    registry = _internal_local_tools_adapter

    # Update allowed permissions if needed
    if allowed_permissions is not None:
        try:
            registry.set_allowed_permissions(allowed_permissions)
        except Exception:
            pass

    # Change workdir if requested
    if workdir is not None:
        try:
            import os
            if not os.path.exists(workdir):
                os.makedirs(workdir, exist_ok=True)
            os.chdir(workdir)
            registry.workdir = workdir
        except Exception:
            pass
    return registry


__all__ = [
    "LocalToolsAdapter",
    "get_local_tools_adapter",
]
