from prompt_toolkit.formatted_text import HTML
from janito.performance_collector import PerformanceCollector
from janito.cli.config import config
from janito.version import __version__ as VERSION


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


def assemble_bindings_line(width):
    return (
        f" <key-label>F1</key-label>: Restart conversation | "
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
        termweb_support = getattr(shell_state, "termweb_support", False)
        termweb_port = (
            shell_state.termweb_port if hasattr(shell_state, "termweb_port") else None
        )
        termweb_status = (
            shell_state.termweb_status
            if hasattr(shell_state, "termweb_status")
            else None
        )
        # Use cached liveness check only (set by background thread in shell_state)
        this_termweb_status = termweb_status
        if not termweb_support:
            this_termweb_status = None
        elif termweb_status == "starting" or termweb_status is None:
            this_termweb_status = termweb_status
        else:
            live_status = (
                shell_state.termweb_live_status
                if hasattr(shell_state, "termweb_live_status")
                else None
            )
            if live_status is not None:
                this_termweb_status = live_status
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

        bindings_line = assemble_bindings_line(width)
        toolbar_text = first_line + "\n" + bindings_line
        # Add termweb status if available, after the F12 line
        if this_termweb_status == "online" and termweb_port:
            toolbar_text += f"\n<termweb> Termweb </termweb>Online<termweb> at <u>http://localhost:{termweb_port}</u></termweb>"
        elif this_termweb_status == "starting":
            toolbar_text += "\n<termweb> Termweb </termweb>Starting"
        elif this_termweb_status == "offline":
            toolbar_text += "\n<termweb> Termweb </termweb>Offline"
        return HTML(toolbar_text)

    return get_toolbar
