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
    Returns a string (rich or pt markup) summarizing message count and last token usage.
    """
    left = f" Messages: {'[' if use_rich else '<'}msg_count{']' if use_rich else '>'}{msg_count}{'[/msg_count]' if use_rich else '</msg_count>'}"
    tokens_part = ""
    if usage:
        prompt_tokens = usage.get("prompt_tokens")
        completion_tokens = usage.get("completion_tokens")
        total_tokens = usage.get("total_tokens")
        tokens_part = (
            f" | Tokens - Prompt: {format_tokens(prompt_tokens, 'tokens_in', use_rich)}, "
            f"Completion: {format_tokens(completion_tokens, 'tokens_out', use_rich)}, "
            f"Total: {format_tokens(total_tokens, 'tokens_total', use_rich)}"
        )
    return f"{left}{tokens_part}"


def print_token_message_summary(console, msg_count=None, usage=None, width=96):
    """Prints the summary using rich markup, using defaults from perf_singleton if not given."""
    if usage is None:
        usage = performance_collector.get_last_request_usage()
    if msg_count is None:
        msg_count = performance_collector.get_total_turns() or 0
    line = format_token_message_summary(msg_count, usage, width, use_rich=True)
    if line.strip():
        console.print(Rule(line))
