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
    max_tokens = None
    if agent is not None and hasattr(agent, "driver") and hasattr(agent.driver, "config"):
        max_tokens = getattr(agent.driver.config, "max_tokens", None)
    tokens_disp = format_tokens(max_tokens, "max-tokens")
    return f" Janito {VERSION} | Provider: <provider>{provider_name}</provider> | Model: <model>{model_name}</model> | Max-Tokens: {tokens_disp} | Role: <role>{role}</role>"

def assemble_second_line(width, usage, msg_count):
    prompt_tokens = usage.get("prompt_tokens") if usage else None
    completion_tokens = usage.get("completion_tokens") if usage else None
    total_tokens = usage.get("total_tokens") if usage else None
    left = f" Messages: <msg_count>{msg_count}</msg_count>"
    tokens_part = ""
    if (
        prompt_tokens is not None
        or completion_tokens is not None
        or total_tokens is not None
    ):
        tokens_part = (
            f" | Tokens - Prompt: {format_tokens(prompt_tokens, 'tokens_in')}, "
            f"Completion: {format_tokens(completion_tokens, 'tokens_out')}, "
            f"Total: {format_tokens(total_tokens, 'tokens_total')}"
        )
    second_line = f"{left}{tokens_part}"
    total_len = len(left) + len(tokens_part)
    if total_len < width:
        padding = " " * (width - total_len)
        second_line = f"{left}{tokens_part}{padding}"
    return second_line

def assemble_bindings_line(width):
    return (
        f' <key-label>F1</key-label>: Restart conversation | '
        f'<key-label>Ctrl-Y</key-label>: Yes | '
        f'<key-label>Ctrl-N</key-label>: No | '
        f'<b>/help</b>: Help | '
        f'<key-label>F12</key-label>: Do It '
    )

def get_toolbar_func(perf: PerformanceCollector, msg_count: int, shell_state):
    from prompt_toolkit.application.current import get_app
    import importlib
    def get_toolbar():
        width = get_app().output.get_size().columns
        provider_name = "?"
        model_name = "?"
        role = "?"
        agent = getattr(shell_state, 'agent', None)
        termweb_port = getattr(shell_state, 'termweb_port', None)
        termweb_status = getattr(shell_state, 'termweb_status', None)
        # Use cached liveness check only (set by background thread in shell_state)
        this_termweb_status = termweb_status
        if termweb_status == "starting" or termweb_status is None:
            this_termweb_status = termweb_status
        else:
            live_status = getattr(shell_state, 'termweb_live_status', None)
            if live_status is not None:
                this_termweb_status = live_status
        if agent is not None:
            if hasattr(agent, "driver"):
                provider_name = getattr(agent.driver, "name", "?")
                model_name = getattr(agent.driver, "model_name", "?")
            if hasattr(agent, "template_vars"):
                role = agent.template_vars.get("role", "?")
        usage = perf.get_last_request_usage()
        first_line = assemble_first_line(provider_name, model_name, role, agent=agent)
        second_line = assemble_second_line(width, usage, msg_count)
        bindings_line = assemble_bindings_line(width)
        toolbar_text = first_line + "\n" + second_line + "\n" + bindings_line
        # Add termweb status if available, after the F12 line
        if this_termweb_status == "online" and termweb_port:
            toolbar_text += f"\n<termweb> Termweb </termweb>Online<termweb> at <u>http://localhost:{termweb_port}</u></termweb>"
        elif this_termweb_status == "starting":
            toolbar_text += "\n<termweb> Termweb </termweb>Starting"
        elif this_termweb_status == "offline":
            toolbar_text += "\n<termweb> Termweb </termweb>Offline"
        return HTML(toolbar_text)
    return get_toolbar
