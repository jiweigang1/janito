from prompt_toolkit.formatted_text import HTML
from janito.performance_collector import PerformanceCollector
from janito.cli.config import config
from janito import __version__ as VERSION


def format_tokens(n, tag=None):
    if n is None:
        return "?"
    if n < 1000:
        val = str(n)
    elif n < 1000000:
        val = f"{n/1000:.1f}k"
    else:
        val = f"{n/1000000:.1f}M"
    return f"<{tag}>{val}</{tag}>" if tag else val


def assemble_first_line(provider_name, model_name, role, agent=None):
    return f" Janito {VERSION} | Provider: <provider>{provider_name}</provider> | Model: <model>{model_name}</model> | Role: <role>{role}</role>"


def assemble_bindings_line(width, permissions=None):
    # permissions: ToolPermissions or None
    def color_state(state):
        if state == "on":
            return 'on '
        else:
            return 'off'
    read_state = color_state("on" if getattr(permissions, "read", False) else "off")
    write_state = color_state("on" if getattr(permissions, "write", False) else "off")
    execute_state = color_state("on" if getattr(permissions, "execute", False) else "off")
    return (
        f" <key-label>CTRL-C</key-label>: Interrupt/Exit | "
        f"<key-label>F1</key-label>: /restart | "
                f"<key-label>F2</key-label>: <key-toggle-{('on' if not getattr(permissions, 'read', False) else 'off')}>/read {'on ' if not getattr(permissions, 'read', False) else 'off'}</key-toggle-{('on' if not getattr(permissions, 'read', False) else 'off')}> | "
                f"<key-label>F3</key-label>: <key-toggle-{('on' if not getattr(permissions, 'write', False) else 'off')}>/write {'on ' if not getattr(permissions, 'write', False) else 'off'}</key-toggle-{('on' if not getattr(permissions, 'write', False) else 'off')}> | "
                f"<key-label>F4</key-label>: <key-toggle-{('on' if not getattr(permissions, 'execute', False) else 'off')}>/execute {'on ' if not getattr(permissions, 'execute', False) else 'off'}</key-toggle-{('on' if not getattr(permissions, 'execute', False) else 'off')}> | "
        f"<b>/help</b>: Help | "
        f"<key-label>F12</key-label>: Do It "
    )


def get_toolbar_func(perf: PerformanceCollector, msg_count: int, shell_state):
    from prompt_toolkit.application.current import get_app
    import importlib

    def get_toolbar():
        width = get_app().output.get_size().columns
        provider_name = "?"
        model_name = "?"
        role = "?"
        agent = shell_state.agent if hasattr(shell_state, "agent") else None
        _support = getattr(shell_state, "_support", False)
        _port = (
            shell_state._port if hasattr(shell_state, "_port") else None
        )
        _status = (
            shell_state._status
            if hasattr(shell_state, "_status")
            else None
        )
        # Use cached liveness check only (set by background thread in shell_state)
        this__status = _status
        if not _support:
            this__status = None
        elif _status == "starting" or _status is None:
            this__status = _status
        else:
            live_status = (
                shell_state._live_status
                if hasattr(shell_state, "_live_status")
                else None
            )
            if live_status is not None:
                this__status = live_status
        if agent is not None:
            # Use agent API to get provider and model name
            provider_name = (
                agent.get_provider_name()
                if hasattr(agent, "get_provider_name")
                else "?"
            )
            model_name = (
                agent.get_model_name() if hasattr(agent, "get_model_name") else "?"
            )
            if hasattr(agent, "template_vars"):
                role = agent.template_vars.get("role", "?")
        usage = perf.get_last_request_usage()
        first_line = assemble_first_line(provider_name, model_name, role, agent=agent)

        # Get current permissions for toolbar state
        try:
            from janito.tools.permissions import get_global_allowed_permissions
            permissions = get_global_allowed_permissions()
        except Exception:
            permissions = None
        bindings_line = assemble_bindings_line(width, permissions)
        toolbar_text = first_line + "\n" + bindings_line
        # Add  status if available, after the F12 line
        if this__status == "online" and _port:
            toolbar_text += f"\n<> Termweb </>Online"
        elif this__status == "starting":
            toolbar_text += "\n<> Termweb </>Starting"
        elif this__status == "offline":
            toolbar_text += "\n<> Termweb </>Offline"
        return HTML(toolbar_text)

    return get_toolbar
