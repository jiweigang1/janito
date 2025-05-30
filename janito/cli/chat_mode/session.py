"""
Session management for Janito Chat CLI.
Defines ChatSession and ChatShellState classes.
"""
import types
from rich.console import Console
from rich.rule import Rule
from prompt_toolkit.history import InMemoryHistory
from janito.cli.chat_mode.shell.input_history import UserInputHistory
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit import PromptSession
from janito.cli.chat_mode.toolbar import get_toolbar_func
from prompt_toolkit.enums import EditingMode
from janito.cli.chat_mode.prompt_style import chat_shell_style
from janito.cli.chat_mode.bindings import KeyBindingsFactory
from janito.cli.chat_mode.shell.commands import handle_command
from janito.cli.chat_mode.shell.autocomplete import ShellCommandCompleter

class ChatShellState:
    def __init__(self, mem_history, conversation_history):
        self.mem_history = mem_history
        self.conversation_history = conversation_history
        self.paste_mode = False
        self.termweb_port = None
        self.termweb_pid = None
        self.termweb_stdout_path = None
        self.termweb_stderr_path = None
        self.livereload_stderr_path = None
        self.termweb_status = "starting"  # Tracks the current termweb status (updated by background thread/UI)
        self.termweb_live_status = None   # 'online', 'offline', updated by background checker
        self.termweb_live_checked_time = None  # datetime.datetime of last status check
        self.last_usage_info = {}
        self.last_elapsed = None
        self.main_agent = {}
        self.mode = None
        self.agent = None
        self.main_agent = None
        self.main_enabled = False

class ChatSession:
    def __init__(self, console, provider_instance=None, llm_driver_config=None, role=None, args=None, verbose_tools=False, verbose_agent=False):
        from janito.cli.prompt_core import PromptHandler as GenericPromptHandler
        self._prompt_handler = GenericPromptHandler(
            args=None,
            conversation_history=None if not hasattr(self, 'shell_state') else self.shell_state.conversation_history,
            provider_instance=provider_instance
        )
        self._prompt_handler.agent = None  # Will be set below if agent exists
        self.console = console
        self.user_input_history = UserInputHistory()
        self.input_dicts = self.user_input_history.load()
        self.mem_history = InMemoryHistory()
        for item in self.input_dicts:
            if isinstance(item, dict) and "input" in item:
                self.mem_history.append_string(item["input"])
        self.provider_instance = provider_instance
        self.llm_driver_config = llm_driver_config
        from janito.agent.setup_agent import create_configured_agent
        agent = create_configured_agent(
    provider_instance=provider_instance,
    llm_driver_config=llm_driver_config,
    role=role,
    verbose_tools=verbose_tools,
    verbose_agent=verbose_agent
)
        self.shell_state = ChatShellState(self.mem_history, [])
        self.shell_state.agent = agent
        self.agent = agent
        from janito.perf_singleton import performance_collector
        self.performance_collector = performance_collector
        self.key_bindings = KeyBindingsFactory.create()
        # Attach agent to prompt handler now that agent is initialized
        self._prompt_handler.agent = self.agent
        self._prompt_handler.conversation_history = self.shell_state.conversation_history

        # TERMWEB logic migrated from runner
        self.termweb_support = False
        if args and not getattr(args, 'no_termweb', False):
            self.termweb_support = True
            from janito.cli.termweb_starter import termweb_start_and_watch
            from janito.cli.config import get_termweb_port
            import threading
            from rich.console import Console
            Console().print("[yellow]Starting termweb in background...[/yellow]")
            self.termweb_lock = threading.Lock()
            termweb_thread = termweb_start_and_watch(self.shell_state, self.termweb_lock, get_termweb_port())
            # Initial status is set to 'starting' by constructor; the watcher will update
            self.termweb_thread = termweb_thread

            # Start a background timer to update live termweb status (for UI responsiveness)
            import threading, datetime
            def update_termweb_liveness():
                while True:
                    with self.termweb_lock:
                        port = getattr(self.shell_state, 'termweb_port', None)
                        if port:
                            try:
                                # is_termweb_running is removed; inline health check here:
                                try:
                                    import http.client
                                    conn = http.client.HTTPConnection("localhost", port, timeout=0.5)
                                    conn.request("GET", "/")
                                    resp = conn.getresponse()
                                    running = (resp.status == 200)
                                except Exception:
                                    running = False
                                self.shell_state.termweb_live_status = 'online' if running else 'offline'
                            except Exception:
                                self.shell_state.termweb_live_status = 'offline'
                            self.shell_state.termweb_live_checked_time = datetime.datetime.now()
                        else:
                            self.shell_state.termweb_live_status = None
                            self.shell_state.termweb_live_checked_time = datetime.datetime.now()
                    # sleep outside lock
                    threading.Event().wait(1.0)
            self._termweb_liveness_thread = threading.Thread(target=update_termweb_liveness, daemon=True)
            self._termweb_liveness_thread.start()
            # No queue or blocking checks; UI (and timer) will observe self.shell_state fields

        elif args and getattr(args, 'no_termweb', False):
            self.shell_state.termweb_status = 'offline'

    def run(self):
        session = self._create_prompt_session()
        self.console.print("[bold green]Type /help for commands. Type /exit or press Ctrl+C to quit.[/bold green]")
        self._chat_loop(session)

    def _chat_loop(self, session):
        self.msg_count = 0
        timer_started = False
        while True:
            if not timer_started:
                timer_started = True
            cmd_input = self._handle_input(session)
            if cmd_input is None:
                break
            if not cmd_input:
                continue
            if self._handle_exit_conditions(cmd_input):
                break
            if cmd_input.startswith("/"):
                handle_command(cmd_input, shell_state=self.shell_state)
                continue
            self.user_input_history.append(cmd_input)
            try:
                self._prompt_handler.run_prompt(cmd_input)
                self.msg_count += 1
                # After prompt, print the stat line using the shared core function
                from janito.formatting_token import print_token_message_summary
                usage = self.performance_collector.get_last_request_usage()
                print_token_message_summary(self.console, self.msg_count, usage)
            except Exception as exc:
                self.console.print(f"[red]Exception in agent: {exc}[/red]")
                import traceback
                self.console.print(traceback.format_exc())

    def _create_prompt_session(self):
        return PromptSession(
            style=chat_shell_style,
            completer=ShellCommandCompleter(),
            history=self.mem_history,
            editing_mode=EditingMode.EMACS,
            key_bindings=self.key_bindings,
            bottom_toolbar=lambda: get_toolbar_func(
                self.performance_collector, 0, self.shell_state
            )(),
        )

    def _handle_input(self, session):
        injected = getattr(self.shell_state, 'injected_input', None)
        if injected is not None:
            cmd_input = injected
            self.shell_state.injected_input = None
        else:
            try:
                cmd_input = session.prompt(HTML("<inputline>💬 </inputline>"))
            except (KeyboardInterrupt, EOFError):
                self._handle_exit()
                return None
        return cmd_input.strip()

    def _handle_exit(self):
        self.console.print("[bold yellow]Exiting chat. Goodbye![/bold yellow]")

    def _handle_exit_conditions(self, cmd_input):
        if cmd_input.lower() in ("/exit", ":q", ":quit"):
            self._handle_exit()
            return True
        return False
