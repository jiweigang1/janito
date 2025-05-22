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

def assemble_second_line(width, usage, msg_count, session_id=None):
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
    session_part = (
        f" | Session ID: <session_id>{session_id}</session_id>" if session_id else ""
    )
    second_line = f"{left}{tokens_part}{session_part}"
    total_len = len(left) + len(tokens_part) + len(session_part)
    if total_len < width:
        padding = " " * (width - total_len)
        second_line = f"{left}{tokens_part}{session_part}{padding}"
    return second_line

def assemble_bindings_line():
    return (
        f' <b>F1</b>: Restart conversation | '
        f'<b>F12</b>: Do It | '
        f'<b>Ctrl-Y</b>: Yes | '
        f'<b>Ctrl-N</b>: No | '
        f'<b>/help</b>: Help | '
    )

def get_toolbar_func(perf: PerformanceCollector, msg_count: int, session_id=None, agent=None):
    from prompt_toolkit.application.current import get_app
    def get_toolbar():
        width = get_app().output.get_size().columns
        provider_name = "?"
        model_name = "?"
        role = "?"
        if agent is not None:
            if hasattr(agent, "driver"):
                provider_name = getattr(agent.driver, "name", "?")
                model_name = getattr(agent.driver, "model_name", "?")
            if hasattr(agent, "template_vars"):
                role = agent.template_vars.get("role", "?")
        usage = perf.get_last_request_usage()
        first_line = assemble_first_line(provider_name, model_name, role, agent=agent)
        second_line = assemble_second_line(width, usage, msg_count, session_id)
        bindings_line = assemble_bindings_line()
        toolbar_text = first_line + "\n" + second_line + "\n" + bindings_line
        return HTML(toolbar_text)
    return get_toolbar
