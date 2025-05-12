"""
PromptHandler: Handles prompt submission and response formatting for janito CLI (one-shot prompt execution).
"""
import time
from janito.version import __version__ as VERSION
from janito.cli.provider_setup import setup_provider, setup_agent
from janito.cli.utils import format_tokens, format_generation_time
from janito.performance_collector import PerformanceCollector
from janito.cli.output import print_verbose_header, print_performance, handle_exception
import janito.tools  # Ensure all tools are registered
from rich.status import Status
from rich.console import Console
import concurrent.futures
from types import SimpleNamespace
from typing import Any, Optional

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
        future, cancel_event = self.agent.chat_async(self.args.user_prompt, raw=getattr(self.args, 'raw', False))
        with Status("[bold cyan]Waiting for LLM response...[/bold cyan]", console=self.console, spinner="dots") as status:
            last_event = None
            try:
                while not future.done():
                    current_event = self.agent.driver.get_latest_event()
                    if current_event and current_event != last_event:
                        status.update(f"[bold cyan]{current_event}[/bold cyan]")
                        last_event = current_event
                    time.sleep(0.1)
            except KeyboardInterrupt:
                cancel_event.set()
                self.console.print("[red]Request cancelled.[/red]")
                return
        end_time = time.perf_counter()
        response = future.result()
        print_performance(start_time, end_time, self.performance_collector, self.args)
        return
