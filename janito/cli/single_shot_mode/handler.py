"""
PromptHandler: Handles prompt submission and response formatting for janito CLI (one-shot prompt execution).
"""

import time
from janito.version import __version__ as VERSION
from janito.cli.prompt_core import PromptHandler as GenericPromptHandler
from janito.cli.verbose_output import (
    print_verbose_header,
    print_performance,
    handle_exception,
)
import janito.tools  # Ensure all tools are registered
from janito.cli.console import shared_console


class PromptHandler:
    def __init__(self, args, provider_instance, llm_driver_config, role=None, exec_enabled=False):
        self.args = args
        self.provider_instance = provider_instance
        self.llm_driver_config = llm_driver_config
        self.role = role
        self.exec_enabled = exec_enabled
        from janito.agent.setup_agent import create_configured_agent

        # DEBUG: Print exec_enabled propagation
        self.agent = create_configured_agent(
            provider_instance=provider_instance,
            llm_driver_config=llm_driver_config,
            role=role,
            verbose_tools=getattr(args, "verbose_tools", False),
            verbose_agent=getattr(args, "verbose_agent", False),
            exec_enabled=exec_enabled,
        )
        # The global permission mask has already been set by the CLI runner.  No
        # additional toggling is necessary here now that the dedicated
        # ``set_execution_tools_enabled()`` helper has been removed.
        self.generic_handler = GenericPromptHandler(
            args, [], provider_instance=provider_instance
        )
        self.generic_handler.agent = self.agent

    def handle(self) -> None:
        import traceback

        user_prompt = " ".join(getattr(self.args, "user_prompt", [])).strip()
        # UTF-8 sanitize user_prompt
        sanitized = user_prompt
        try:
            sanitized.encode("utf-8")
        except UnicodeEncodeError:
            sanitized = sanitized.encode("utf-8", errors="replace").decode("utf-8")
            shared_console.print(
                "[yellow]Warning: Some characters in your input were not valid UTF-8 and have been replaced.[/yellow]"
            )
        try:
            self.generic_handler.handle_prompt(
                sanitized,
                args=self.args,
                print_header=True,
                raw=getattr(self.args, "raw", False),
            )
            if hasattr(self.args, "verbose_agent") and self.args.verbose_agent:
                print("[debug] handle_prompt() completed without exception.")
        except Exception as e:
            print(
                f"[error] Exception occurred in handle_prompt: {type(e).__name__}: {e}"
            )
            traceback.print_exc()
        self._post_prompt_actions()

    def _post_prompt_actions(self):
        final_event = getattr(self.agent, "last_event", None)
        if final_event is not None:
            self._print_exit_reason_and_parts(final_event)
            # --- BEGIN: Print token info in rich rule if --verbose is set ---
            if hasattr(self.args, "verbose") and self.args.verbose:
                from janito.perf_singleton import performance_collector

                token_info = performance_collector.get_last_request_usage()
                from rich.rule import Rule
                from rich import print as rich_print
                from janito.cli.utils import format_tokens

                if token_info:
                    if isinstance(token_info, dict):
                        token_str = " | ".join(
                            f"{k}: {format_tokens(v) if isinstance(v, int) else v}"
                            for k, v in token_info.items()
                        )
                    else:
                        token_str = str(token_info)
                    rich_print(Rule(f"[bold cyan]Token Usage[/bold cyan] {token_str}"))
                else:
                    rich_print(Rule("[cyan]No token usage info available.[/cyan]"))
        else:
            shared_console.print("[yellow]No output produced by the model.[/yellow]")
        self._cleanup_driver_and_console()

    def _print_exit_reason_and_parts(self, final_event):
        exit_reason = (
            getattr(final_event, "metadata", {}).get("exit_reason")
            if hasattr(final_event, "metadata")
            else None
        )
        if exit_reason:
            print(f"[bold yellow]Exit reason: {exit_reason}[/bold yellow]")
        parts = getattr(final_event, "parts", None)
        if not exit_reason:
            if parts is None or len(parts) == 0:
                shared_console.print(
                    "[yellow]No output produced by the model.[/yellow]"
                )
            else:
                if hasattr(self.args, "verbose_agent") and self.args.verbose_agent:
                    print(
                        "[yellow]No user-visible output. Model returned the following parts:"
                    )
                    for idx, part in enumerate(parts):
                        print(
                            f"  [part {idx}] type: {type(part).__name__} | content: {getattr(part, 'content', repr(part))}"
                        )

    def _cleanup_driver_and_console(self):
        if hasattr(self.agent, "join_driver"):
            if (
                hasattr(self.agent, "input_queue")
                and self.agent.input_queue is not None
            ):
                self.agent.input_queue.put(None)
            self.agent.join_driver()
        try:
            shared_console.file.flush()
        except Exception:
            pass
        try:
            import sys

            sys.stdout.flush()
        except Exception:
            pass
        # If event logger is active, flush event log
