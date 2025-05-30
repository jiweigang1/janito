"""
Core PromptHandler: Handles prompt submission and response formatting for janito CLI (shared by single and chat modes).
"""
import time
from janito.version import __version__ as VERSION
from janito.performance_collector import PerformanceCollector
from rich.status import Status
from rich.console import Console
from typing import Any, Optional, Callable
from janito.driver_events import RequestStarted, RequestFinished, RequestError, EmptyResponseEvent
from janito.tools.tool_events import ToolCallError
import threading
from janito.cli.verbose_output import print_verbose_header
from janito.event_bus import event_bus as global_event_bus

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
        self.temperature = args.temperature if hasattr(args, 'temperature') else None
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
        from janito.tools.tool_events import ToolCallFinished
        # Print tool result if ToolCallFinished event is received
        if isinstance(inner_event, ToolCallFinished):
            # Print result if verbose_tools is enabled or always for user visibility
            if hasattr(self.args, 'verbose_tools') and self.args.verbose_tools:
                self.console.print(f"[cyan][tools-adapter] Tool '{inner_event.tool_name}' result:[/cyan] {inner_event.result}")
            else:
                self.console.print(inner_event.result)
            return None
        if isinstance(inner_event, RequestFinished):
            status.update("[bold green]Received response![bold green]")
            return 'break'
        elif isinstance(inner_event, RequestError):
            error_msg = inner_event.error if hasattr(inner_event, 'error') else 'Unknown error'
            if (
                'Status 429' in error_msg and
                'Service tier capacity exceeded for this model' in error_msg
            ):
                status.update("[yellow]Service tier capacity exceeded, retrying...[yellow]")
                return 'break'
            status.update(f"[bold red]Error: {error_msg}[bold red]")
            self.console.print(f"[red]Error: {error_msg}[red]")
            return 'break'
        elif isinstance(inner_event, ToolCallError):
            error_msg = inner_event.error if hasattr(inner_event, 'error') else 'Unknown tool error'
            tool_name = inner_event.tool_name if hasattr(inner_event, 'tool_name') else 'unknown'
            status.update(f"[bold red]Tool Error in '{tool_name}': {error_msg}[bold red]")
            self.console.print(f"[red]Tool Error in '{tool_name}': {error_msg}[red]")
            return 'break'
        elif isinstance(inner_event, EmptyResponseEvent):
            details = inner_event.details if hasattr(inner_event, 'details') and inner_event.details is not None else {}
            block_reason = details.get('block_reason')
            block_msg = details.get('block_reason_message')
            msg = details.get('message', 'LLM returned an empty or incomplete response.')
            driver_name = inner_event.driver_name if hasattr(inner_event, 'driver_name') else 'unknown driver'
            if block_reason or block_msg:
                status.update(f"[bold yellow]Blocked by driver: {driver_name} | {block_reason or ''} {block_msg or ''}[bold yellow]")
                self.console.print(f"[yellow]Blocked by driver: {driver_name} (empty response): {block_reason or ''}\n{block_msg or ''}[/yellow]")
            else:
                status.update(f"[yellow]LLM produced no output for this request (driver: {driver_name}).[/yellow]")
                self.console.print(f"[yellow]Warning: {msg} (driver: {driver_name})[/yellow]")
            return 'break'
        # Report unknown event types
        event_type = type(inner_event).__name__
        self.console.print(f"[yellow]Warning: Unknown event type encountered: {event_type}[yellow]")
        return None

    def _process_event_iter(self, event_iter, on_event):
        for event in event_iter:
            # Handle exceptions from generation thread
            if isinstance(event, dict) and event.get('type') == 'exception':
                self.console.print("[red]Exception in generation thread:[red]")
                self.console.print(event.get('traceback', 'No traceback available'))
                break
            if on_event:
                on_event(event)
            if isinstance(event, RequestStarted):
                with Status("[bold cyan]Waiting for LLM response...[bold cyan]", console=self.console, spinner="dots") as status:
                    status.update("[bold cyan]Waiting for LLM response...[bold cyan]")
                    for inner_event in event_iter:
                        result = self._handle_inner_event(inner_event, on_event, status)
                        if result == 'break':
                            break
                # After exiting spinner, continue with next events (if any)
            # Handle other event types outside the spinner if needed
            elif isinstance(event, EmptyResponseEvent):
                details = event.details if hasattr(event, 'details') and event.details is not None else {}
                block_reason = details.get('block_reason')
                block_msg = details.get('block_reason_message')
                msg = details.get('message', 'LLM returned an empty or incomplete response.')
                driver_name = event.driver_name if hasattr(event, 'driver_name') else 'unknown driver'
                if block_reason or block_msg:
                    self.console.print(f"[yellow]Blocked by driver: {driver_name} (empty response): {block_reason or ''}\n{block_msg or ''}[/yellow]")
                else:
                    self.console.print(f"[yellow]Warning: {msg} (driver: {driver_name})[/yellow]")
            else:
                pass

    def handle_prompt(self, user_prompt, args=None, print_header=True, raw=False, on_event=None):
        # args defaults to self.args for compatibility in interactive mode
        args = args if args is not None else self.args if hasattr(self, 'args') else None
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
        Handles a single prompt, using the blocking event-driven chat interface.
        Optionally takes an on_event callback for custom event handling.
        """
        from queue import Queue
        local_event_bus = Queue()
        try:
            # Call the new blocking chat() method
            if hasattr(self.args, 'verbose_agent') and self.args.verbose_agent:
                print("[prompt_core][DEBUG] Calling agent.chat()...")
            final_event = self.agent.chat(prompt=user_prompt, bus=local_event_bus)
            if hasattr(self.args, 'verbose_agent') and self.args.verbose_agent:
                print(f"[prompt_core][DEBUG] agent.chat() returned: {final_event}")
            # Drain and process all events from the bus
            while not local_event_bus.empty():
                event = local_event_bus.get()
                # Publish to global event bus
                global_event_bus.publish(event)
                if on_event:
                    on_event(event)
            # Optionally process the final event
            if hasattr(self.args, 'verbose_agent') and self.args.verbose_agent:
                print("[prompt_core][DEBUG] Received final_event from agent.chat:")
                print(f"  [prompt_core][DEBUG] type={type(final_event)}")
                print(f"  [prompt_core][DEBUG] content={final_event}")
            if on_event and final_event is not None:
                on_event(final_event)
                global_event_bus.publish(final_event)
        except KeyboardInterrupt:
            self.console.print("[red]Request interrupted.[red]")

    def run_prompts(self, prompts: list, raw: bool = False, on_event: Optional[Callable] = None) -> None:
        """
        Handles multiple prompts in sequence, collecting performance data for each.
        """
        for prompt in prompts:
            self.run_prompt(prompt, raw=raw, on_event=on_event)
        # No return value
