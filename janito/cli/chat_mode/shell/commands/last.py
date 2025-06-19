from janito.performance_collector import PerformanceCollector
from rich.tree import Tree
from rich.console import Console
from rich import print as rprint
import datetime

# TODO: Replace this with your actual collector instance retrieval
# For example, if you have a global or singleton:
# from janito.app_context import performance_collector as collector
from janito.perf_singleton import performance_collector as collector
from janito.cli.chat_mode.shell.commands.base import ShellCmdHandler
from janito.cli.console import shared_console


def _event_timestamp(event):
    if hasattr(event, "timestamp"):
        try:
            ts = float(getattr(event, "timestamp", 0))
            return f" [dim]{datetime.datetime.fromtimestamp(ts)}[/dim]"
        except Exception:
            return ""
    return ""


def _event_tool_name(event):
    return (
        f" [cyan]{getattr(event, 'tool_name', '')}[/cyan]"
        if hasattr(event, "tool_name")
        else ""
    )


def _event_params(event):
    return (
        f" Params: {getattr(event, 'params', '')}" if hasattr(event, "params") else ""
    )


def _event_result(event):
    return (
        f" Result: {getattr(event, 'result', '')}" if hasattr(event, "result") else ""
    )


def _event_error(event):
    return (
        f" [red]Error: {getattr(event, 'error')}[/red]"
        if hasattr(event, "error") and getattr(event, "error", None)
        else ""
    )


def _event_message(event):
    return (
        f" [yellow]Message: {getattr(event, 'message')}[/yellow]"
        if hasattr(event, "message")
        else ""
    )


def _event_subtype(event):
    return (
        f" [magenta]Subtype: {getattr(event, 'subtype')}[/magenta]"
        if hasattr(event, "subtype")
        else ""
    )


def _event_status(event):
    return (
        f" [blue]Status: {getattr(event, 'status')}[/blue]"
        if hasattr(event, "status")
        else ""
    )


def _event_duration(event):
    return (
        f" [green]Duration: {getattr(event, 'duration')}[/green]"
        if hasattr(event, "duration")
        else ""
    )


def format_event(event_tuple, parent_tree=None):
    event_type, event = event_tuple
    desc = f"[bold]{event_type}[/bold]"
    # Modular logic for each possible component
    desc += _event_timestamp(event)
    desc += _event_tool_name(event)
    desc += _event_params(event)
    desc += _event_result(event)
    desc += _event_error(event)
    desc += _event_message(event)
    desc += _event_subtype(event)
    desc += _event_status(event)
    desc += _event_duration(event)
    if parent_tree is not None:
        node = parent_tree.add(desc)
    else:
        node = Tree(desc)
    return node


def drill_down_last_generation():
    events = collector.get_all_events()
    # Find the last RequestStarted
    last_gen_start = None
    for i in range(len(events) - 1, -1, -1):
        if events[i][0] == "RequestStarted":
            last_gen_start = i
            break
    if last_gen_start is None:
        rprint("[red]No generations found.[/red]")
        return
    # Find the next GenerationFinished after last_gen_start
    for j in range(last_gen_start + 1, len(events)):
        if events[j][0] == "GenerationFinished":
            last_gen_end = j
            break
    else:
        last_gen_end = len(events) - 1
    gen_events = events[last_gen_start : last_gen_end + 1]
    tree = Tree("[bold green]Last Generation Details[/bold green]")
    for evt in gen_events:
        format_event(evt, tree)
    console = Console()
    console.print(tree)


class LastShellHandler(ShellCmdHandler):
    help_text = (
        "Show details of the last generation, with drill-down of tool executions."
    )

    def run(self):
        drill_down_last_generation()
