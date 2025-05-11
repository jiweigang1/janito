"""
PromptHandler: Handles prompt submission and response formatting for janito CLI.
"""
import time
from janito.version import __version__ as VERSION
from janito.provider_registry import ProviderRegistry
from janito.provider_config import ProviderConfigManager
from janito.performance_tracker import PerformanceTracker
import janito.tools  # Ensure all tools are registered

# Keep a global reference to RichTerminalReporter to ensure event handling for Rich console output.
from janito.rich_terminal_reporter import RichTerminalReporter
_rich_ui_manager = RichTerminalReporter()

class PromptHandler:
    def __init__(self, args):
        self.args = args
        global _rich_ui_manager
        if _rich_ui_manager is None:
            _rich_ui_manager = RichTerminalReporter(raw_mode=getattr(args, 'raw', False))
        self.provider_registry = ProviderRegistry()
        self.provider_config_mgr = ProviderConfigManager()
        self.provider_name = None
        self.provider_cls = None
        self.agent = None
        self.thinking_budget = None
        self.performance_tracker = PerformanceTracker()

    def handle(self):
        self.provider_name = self.provider_registry.select_provider(self.args)
        if not self.provider_name:
            return
        self._setup_provider()
        self._setup_agent()
        self._print_verbose_header()
        start_time = time.perf_counter()
        response = self.agent.chat(self.args.user_prompt, raw=getattr(self.args, 'raw', False))
        end_time = time.perf_counter()
        content = self._extract_content(response)
        self._print_performance(start_time, end_time)
        if getattr(self.args, 'raw', False):
            return response
        else:
            return content

    def _setup_provider(self):
        from janito.providers.registry import LLMProviderRegistry
        self.provider_cls = LLMProviderRegistry.get(self.provider_name)
        # Determine thinking_budget: CLI > config > default (0)
        thinking_budget = getattr(self.args, 'thinking_budget', None)
        if thinking_budget is None:
            thinking_budget = self.provider_config_mgr.get_thinking_budget(self.provider_name)
        else:
            thinking_budget = int(thinking_budget)
        self.thinking_budget = thinking_budget

    def _setup_agent(self):
        self.agent = self.provider_cls().create_agent(
            system_prompt=getattr(self.args, 'system', None),
            thinking_budget=self.thinking_budget
        )

    def _print_verbose_header(self):
        if getattr(self.args, 'verbose', False):
            from rich import print as rich_print
            rich_print(f"[cyan]Janito {VERSION} | Driver: {self.agent.driver.get_name()} | thinking_budget={self.thinking_budget}[/cyan]")

    @staticmethod
    def _extract_content(response):
        try:
            if hasattr(response, 'choices') and hasattr(response.choices[0], 'message'):
                # OpenAI style
                return response.choices[0].message.content
            elif hasattr(response, 'candidates') and response.candidates:
                # Gemini style
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts') and candidate.content.parts:
                    for part in candidate.content.parts:
                        if hasattr(part, 'text') and part.text:
                            return part.text
                    return str(response)
                else:
                    return str(response)
            else:
                return str(response)
        except Exception:
            return str(response)

    def _print_performance(self, start_time, end_time):
        generation_time_ns = (end_time - start_time) * 1e9
        generation_time_ms = generation_time_ns / 1e6
        if getattr(self.args, 'verbose', False):
            from rich import print as rich_print
            formatted_time = self._format_generation_time(generation_time_ms)
            events = self.performance_tracker.get_all_events()
            last_event = events[-1] if events else None
            if last_event:
                rich_print(f"[cyan]Generation Time: {formatted_time} | Duration: {last_event['duration']:.3f}s | Status: {last_event['status']}[/cyan]")
                # Print token usage by category in verbose mode
                # Try to print detailed usage if available
                detailed_usage = None
                if 'response' in last_event and hasattr(last_event['response'], 'usage') and last_event['response'].usage:
                    detailed_usage = last_event['response'].usage
                if detailed_usage:
                    from rich.pretty import pprint
                    rich_print(f"[cyan]Usage (detailed):[/cyan]")
                    pprint(detailed_usage)
                else:
                    token_usage = self.performance_tracker.get_last_token_usage()
                    if token_usage and any(count > 0 for count in token_usage.values()):
                        token_str = ', '.join(f'{category}={count}' for category, count in token_usage.items())
                        rich_print(f"[cyan]Usage: {token_str}[/cyan]")
            else:
                rich_print(f"[cyan]Generation Time: {formatted_time} | No performance data available.[/cyan]")

    @staticmethod
    def _format_generation_time(generation_time_ms):
        minutes = int(generation_time_ms // 60000)
        seconds = int((generation_time_ms % 60000) // 1000)
        milliseconds = int(generation_time_ms % 1000)
        formatted_time = ""
        if minutes > 0:
            formatted_time += f"{minutes}m "
        if seconds > 0:
            formatted_time += f"{seconds}s "
        formatted_time += f"[{int(generation_time_ms)} ms]"
        return formatted_time

    def _handle_exception(self, e):
        try:
            from rich import print as rich_print
            rich_print(f"[bold red]Error:[/bold red] {e}")
        except ImportError:
            print(f"Error: {e}")
        return

# For backward compatibility

def handle_prompt(args):
    """Legacy function for handling prompt, now uses PromptHandler class."""
    PromptHandler(args).handle()
