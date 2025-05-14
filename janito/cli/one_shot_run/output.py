"""
Output formatting and error handling for janito CLI (one-shot run).
"""
from rich import print as rich_print
from rich.align import Align
from rich.panel import Panel
from janito.version import __version__ as VERSION
from janito.cli.utils import format_tokens

def print_verbose_header(agent, args):
    if getattr(args, 'verbose', False):
        info_line = f"Janito {VERSION} | Provider: {agent.driver.provider_name} | Model: {agent.driver.model_name} | Driver: {agent.driver.__class__.__module__.split('.')[-2]}"
        if getattr(args, 'think', False):
            info_line += " | Thinking ON"
        rich_print(Panel(Align(f"[cyan]{info_line}[/cyan]", align="center"), style="on grey11", expand=True))

def print_performance(start_time, end_time, performance_collector, args):
    if start_time is None or end_time is None:
        generation_time_ns = None
    else:
        generation_time_ns = (end_time - start_time) * 1e9
    if getattr(args, 'verbose', False):
        from rich.table import Table
        from rich.style import Style
        from rich import box
        total_requests = performance_collector.get_total_requests()
        avg_duration = performance_collector.get_average_duration()
        status_counts = performance_collector.get_status_counts()
        token_usage = performance_collector.get_token_usage()
        error_count = performance_collector.get_error_count()
        avg_turns = performance_collector.get_average_turns()
        content_parts = performance_collector.get_content_part_count()

        left = []
        right = []
        right.append(("[bold]Total Requests[/bold]", f"{total_requests}"))
        left.append(("[bold]Avg Duration[/bold]", f"{avg_duration:.3f}s"))
        right.append(("[bold]Status Counts[/bold]", ', '.join(f"{k}: {v}" for k, v in status_counts.items()) if status_counts else "-"))
        if token_usage:
            usage_str = ', '.join(f"{k.removesuffix('_token_count').removesuffix('_tokens')}: {format_tokens(v)}" for k, v in token_usage.items())
        else:
            usage_str = "-"
        left.append(("[bold]Token Usage[/bold]", usage_str))
        right.append(("[bold]Avg Turns[/bold]", f"{avg_turns:.2f}" if avg_turns > 0 else "-"))
        left.append(("[bold]Content Parts[/bold]", f"{content_parts}" if content_parts > 0 else "-"))
        right.append(("[bold]Errors[/bold]", f"{error_count}" if error_count > 0 else "-"))

        total_tool_events = performance_collector.get_total_tool_events()
        tool_names_counter = performance_collector.get_tool_names_counter()
        tool_error_count = performance_collector.get_tool_error_count()
        tool_error_messages = performance_collector.get_tool_error_messages()
        tool_action_counter = performance_collector.get_tool_action_counter()
        tool_subtype_counter = performance_collector.get_tool_subtype_counter()

        tool_names_str = ', '.join(f"{k}: {v}" for k, v in tool_names_counter.items()) if tool_names_counter else "-"
        tool_actions_str = ', '.join(f"{k.split('.')[-1]}: {v}" for k, v in tool_action_counter.items()) if tool_action_counter else "-"
        tool_subtypes_str = ', '.join(f"{k}: {v}" for k, v in tool_subtype_counter.items()) if tool_subtype_counter else "-"
        tool_errors_str = f"{tool_error_count}"
        tool_error_msgs_str = '\n'.join(tool_error_messages[:2]) + ("\n..." if len(tool_error_messages) > 2 else "") if tool_error_count else "-"

        left.append(("[bold]Tool Events[/bold]", f"{total_tool_events}"))
        right.append(("[bold]Tool Usage[/bold]", tool_names_str))
        left.append(("[bold]Tool Errors[/bold]", tool_errors_str))

        max_len = max(len(left), len(right))
        while len(left) < max_len:
            left.append(("", ""))
        while len(right) < max_len:
            right.append(("", ""))

        table = Table(show_header=False, box=box.SIMPLE, pad_edge=False, style=Style(color="cyan"), expand=False)
        table.add_column(justify="right")
        table.add_column(justify="left")
        table.add_column(justify="right")
        table.add_column(justify="left")
        for (l_key, l_val), (r_key, r_val) in zip(left, right):
            table.add_row(l_key, l_val, r_key, r_val)
        if total_requests == 0:
            table.add_row("[bold]Info[/bold]", "No performance data available.", "", "")
        rich_print(Panel(table, style="on grey11", expand=True))

def handle_exception(e):
    try:
        rich_print(f"[bold red]Error:[/bold red] {e}")
    except ImportError:
        print(f"Error: {e}")
    return
