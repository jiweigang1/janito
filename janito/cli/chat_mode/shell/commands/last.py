from janito.performance_collector import PerformanceCollector
from rich.tree import Tree
from rich.console import Console
from rich import print as rprint
import datetime

# TODO: Replace this with your actual collector instance retrieval
# For example, if you have a global or singleton:
# from janito.app_context import performance_collector as collector
from janito.perf_singleton import performance_collector as collector

def format_event(event_tuple, parent_tree=None):
    event_type, event = event_tuple
    desc = f"[bold]{event_type}[/bold]"
    # Add timestamp if available
    if hasattr(event, 'timestamp'):
        try:
            ts = float(getattr(event, 'timestamp', 0))
            desc += f" [dim]{datetime.datetime.fromtimestamp(ts)}[/dim]"
        except Exception:
            pass
    # Add tool name if available
    if hasattr(event, 'tool_name'):
        desc += f" [cyan]{getattr(event, 'tool_name', '')}[/cyan]"
    # Add params if available
    if hasattr(event, 'params'):
        desc += f" Params: {getattr(event, 'params', '')}"
    # Add result if available
    if hasattr(event, 'result'):
        desc += f" Result: {getattr(event, 'result', '')}"
    # Add error if available
    if hasattr(event, 'error') and getattr(event, 'error', None):
        desc += f" [red]Error: {getattr(event, 'error')}[/red]"
    # Add message if available
    if hasattr(event, 'message'):
        desc += f" [yellow]Message: {getattr(event, 'message')}[/yellow]"
    # Add subtype if available
    if hasattr(event, 'subtype'):
        desc += f" [magenta]Subtype: {getattr(event, 'subtype')}[/magenta]"
    # Add status if available
    if hasattr(event, 'status'):
        desc += f" [blue]Status: {getattr(event, 'status')}[/blue]"
    # Add duration if available
    if hasattr(event, 'duration'):
        desc += f" [green]Duration: {getattr(event, 'duration')}[/green]"

    if parent_tree is not None:
        node = parent_tree.add(desc)
    else:
        node = Tree(desc)
    return node

def drill_down_last_generation():
    events = collector.get_all_events()
    # Find the last RequestStarted
    last_gen_start = None
    for i in range(len(events)-1, -1, -1):
        if events[i][0] == 'RequestStarted':
            last_gen_start = i
            break
    if last_gen_start is None:
        rprint("[red]No generations found.[/red]")
        return
    # Find the next GenerationFinished after last_gen_start
    for j in range(last_gen_start+1, len(events)):
        if events[j][0] == 'GenerationFinished':
            last_gen_end = j
            break
    else:
        last_gen_end = len(events) - 1
    gen_events = events[last_gen_start:last_gen_end+1]
    tree = Tree("[bold green]Last Generation Details[/bold green]")
    for evt in gen_events:
        format_event(evt, tree)
    console = Console()
    console.print(tree)

from janito.cli.chat_mode.shell.commands.base import ShellCmdHandler
from janito.cli.console import shared_console

def drill_down_last_generation():
    # ... (existing logic)
    pass

class LastHandler(ShellCmdHandler):
    help_text = "Show details of the last generation, with drill-down of tool executions."

    def run(self):
        drill_down_last_generation()
