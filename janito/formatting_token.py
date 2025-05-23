"""
Token summary formatter for rich and pt markup.
- Used to display token/message counters after completions.
"""
from janito.perf_singleton import performance_collector

from rich.rule import Rule

def format_tokens(n, tag=None, use_rich=False):
    if n is None:
        return "?"
    if n < 1000:
        val = str(n)
    elif n < 1000000:
        val = f"{n/1000:.1f}k"
    else:
        val = f"{n/1000000:.1f}M"
    if tag:
        if use_rich:
            return f"[{tag}]{val}[/{tag}]"
        else:
            return f"<{tag}>{val}</{tag}>"
    return val

def format_token_message_summary(msg_count, usage, width=96, use_rich=False):
    """
    Returns a string (rich or pt markup) summarizing message & token counts.
    """
    prompt_tokens = usage.get("prompt_tokens") if usage else None
    completion_tokens = usage.get("completion_tokens") if usage else None
    total_tokens = usage.get("total_tokens") if usage else None
    left = f" Messages: {'[' if use_rich else '<'}msg_count{']' if use_rich else '>'}{msg_count}{'[/msg_count]' if use_rich else '</msg_count>'}"
    tokens_part = ""
    if (
        prompt_tokens is not None
        or completion_tokens is not None
        or total_tokens is not None
    ):
        tokens_part = (
            f" | Tokens - Prompt: {format_tokens(prompt_tokens, 'tokens_in', use_rich)}, "
            f"Completion: {format_tokens(completion_tokens, 'tokens_out', use_rich)}, "
            f"Total: {format_tokens(total_tokens, 'tokens_total', use_rich)}"
        )
    second_line = f"{left}{tokens_part}"
    total_len = len(second_line)
    if total_len < width:
        padding = " " * (width - total_len)
        second_line = f"{second_line}{padding}"
    return second_line


def print_token_message_summary(console, msg_count=None, usage=None, width=96):
    """Prints the summary using rich markup, using defaults from perf_singleton if not given."""
    if usage is None:
        usage = performance_collector.get_last_request_usage()
    if msg_count is None:
        msg_count = performance_collector.get_total_turns() or 0
    line = format_token_message_summary(msg_count, usage, width, use_rich=True)
    if line.strip():
        console.print(Rule(line))
