"""
PromptHandler: Handles prompt submission and response formatting for janito CLI (one-shot prompt execution).
"""
import time
from janito.version import __version__ as VERSION
from janito.cli.provider_setup import setup_provider, setup_agent
from janito.cli.utils import format_tokens, format_generation_time
from janito.performance_collector import PerformanceCollector
from janito.cli.one_shot_run.output import print_verbose_header, print_performance, handle_exception
import janito.tools  # Ensure all tools are registered
from rich.status import Status
from rich.console import Console
from typing import Any, Optional
from janito.driver_events import GenerationStarted, GenerationFinished, RequestStarted, RequestFinished, RequestError, ContentPartFound
import janito.driver_events as driver_events
import threading

class StatusRef:
    def __init__(self):
        self.status = None

class PromptHandler:
    args: Any
    provider_name: Optional[str]
    provider_cls: Any
    agent: Any
    thinking_budget: Any
    performance_collector: PerformanceCollector
    console: Console

    def __init__(self, args: Any) -> None:
        self.args = args
        self.provider_name = None
        self.provider_cls = None
        self.agent = None
        self.thinking_budget = None
        self.performance_collector = PerformanceCollector()
        self.console = Console()

    def handle(self) -> None:
        self.provider_name = setup_provider(self.args)
        if not self.provider_name:
            return
        self.provider_cls, self.thinking_budget = setup_provider(self.args, return_class=True)
        self.agent = setup_agent(self.provider_cls, self.args, self.thinking_budget)
        print_verbose_header(self.agent, self.args)
        start_time = time.perf_counter()
        try:
            event_iter = self.agent.chat_async(self.args.user_prompt, raw=getattr(self.args, 'raw', False))
            event_iter = iter(event_iter)
            for event in event_iter:
                if isinstance(event, RequestStarted):
                    with Status("[bold cyan]Waiting for LLM response...[/bold cyan]", console=self.console, spinner="dots") as status:
                        status.update("[bold cyan]Waiting for LLM response...[/bold cyan]")
                        for inner_event in event_iter:
                            if isinstance(inner_event, RequestFinished):
                                status.update("[bold green]Received response![/bold green]")
                                break
                            elif isinstance(inner_event, RequestError):
                                status.update(f"[bold red]Error: {getattr(inner_event, 'error', 'Unknown error')}[/bold red]")
                                break
                        # After exiting spinner, continue with next events (if any)
                # You can handle other event types outside the spinner here if needed
        except KeyboardInterrupt:
            self.console.print("[red]Request cancelled.[/red]")
            return
        end_time = time.perf_counter()
        print_performance(start_time, end_time, self.performance_collector, self.args)
