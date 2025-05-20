"""
Generic PromptHandler: Handles prompt submission and response formatting for janito CLI.
Supports both one-shot and multi-prompt scenarios.
"""
import time
from janito.version import __version__ as VERSION
from janito.cli.provider_setup import setup_agent
from janito.performance_collector import PerformanceCollector
from rich.status import Status
from rich.console import Console
from typing import Any, Optional, Callable
from janito.driver_events import RequestStarted, RequestFinished, RequestError
from janito.tool_events import ToolCallError
import threading

from janito.provider_config import validate_mandatory_provider_config
from janito.cli.single_shot_mode.output import print_verbose_header

class StatusRef:
    def __init__(self):
        self.status = None

class PromptHandler:
    args: Any
    agent: Any
    performance_collector: PerformanceCollector
    console: Console
    provider_instance: Any

    def __init__(self, args: Any, conversation_history, provider_instance) -> None:
        validate_mandatory_provider_config()
        self.temperature = getattr(args, 'temperature', None)
        """
        Initialize PromptHandler.
        :param args: CLI or programmatic arguments for provider/model selection, etc.
        :param conversation_history: LLMConversationHistory object for multi-turn chat mode.
        :param provider_instance: An initialized provider instance.
        """
        self.args = args
        self.conversation_history = conversation_history
        self.provider_instance = provider_instance
        self.agent = None
        from janito.perf_singleton import performance_collector
        self.performance_collector = performance_collector
        self.console = Console()

    def _handle_inner_event(self, inner_event, on_event, status):
        if on_event:
            on_event(inner_event)
        if isinstance(inner_event, RequestFinished):
            status.update("[bold green]Received response![/bold green]")
            return 'break'
        elif isinstance(inner_event, RequestError):
            error_msg = getattr(inner_event, 'error', 'Unknown error')
            if (
                'Status 429' in error_msg and
                'Service tier capacity exceeded for this model' in error_msg
            ):
                status.update("[yellow]Service tier capacity exceeded, retrying...[/yellow]")
                return 'break'
            status.update(f"[bold red]Error: {error_msg}[/bold red]")
            self.console.print(f"[red]Error: {error_msg}[/red]")
            return 'break'
        elif isinstance(inner_event, ToolCallError):
            error_msg = getattr(inner_event, 'error', 'Unknown tool error')
            tool_name = getattr(inner_event, 'tool_name', 'unknown')
            status.update(f"[bold red]Tool Error in '{tool_name}': {error_msg}[/bold red]")
            self.console.print(f"[red]Tool Error in '{tool_name}': {error_msg}[/red]")
            return 'break'
        # Report unknown event types
        event_type = type(inner_event).__name__
        self.console.print(f"[yellow]Warning: Unknown event type encountered: {event_type}[/yellow]")
        return None

    def _process_event_iter(self, event_iter, on_event):
        for event in event_iter:
            # Handle exceptions from generation thread
            if isinstance(event, dict) and event.get('type') == 'exception':
                self.console.print("[red]Exception in generation thread:[/red]")
                self.console.print(event.get('traceback', 'No traceback available'))
                break
            if on_event:
                on_event(event)
            if isinstance(event, RequestStarted):
                with Status("[bold cyan]Waiting for LLM response...[/bold cyan]", console=self.console, spinner="dots") as status:
                    status.update("[bold cyan]Waiting for LLM response...[/bold cyan]")
                    for inner_event in event_iter:
                        result = self._handle_inner_event(inner_event, on_event, status)
                        if result == 'break':
                            break
                # After exiting spinner, continue with next events (if any)
            # Handle other event types outside the spinner if needed
            else:
                pass

    def handle_prompt(self, user_prompt, args=None, print_header=True, raw=False, on_event=None):
        # args defaults to self.args for compatibility in interactive mode
        args = args if args is not None else getattr(self, 'args', None)
        # Join/cleanup prompt
        if isinstance(user_prompt, list):
            user_prompt = " ".join(user_prompt).strip()
        else:
            user_prompt = str(user_prompt).strip() if user_prompt is not None else ''
        if not user_prompt:
            raise ValueError("No user prompt was provided!")
        if print_header and hasattr(self, 'agent') and args is not None:
            print_verbose_header(self.agent, args)
        self.run_prompt(user_prompt, raw=raw, on_event=on_event)

    def run_prompt(self, user_prompt: str, raw: bool = False, on_event: Optional[Callable] = None) -> None:
        """
        Handles a single prompt, iterating through agent events using the streaming/event-driven chat interface.
        Optionally takes an on_event callback for custom event handling.
        """
        import threading
        cancel_event = threading.Event()
        try:
            event_iter = self.agent.chat(user_prompt, raw=raw, cancel_event=cancel_event)
            event_iter = iter(event_iter)
            self._process_event_iter(event_iter, on_event)
        except KeyboardInterrupt:
            cancel_event.set()
            self.console.print("[red]Request cancelled.[/red]")
        # No return value; performance timing removed

    def run_prompts(self, prompts: list, raw: bool = False, on_event: Optional[Callable] = None) -> None:
        """
        Handles multiple prompts in sequence, collecting performance data for each.
        """
        for prompt in prompts:
            self.run_prompt(prompt, raw=raw, on_event=on_event)
        # No return value
