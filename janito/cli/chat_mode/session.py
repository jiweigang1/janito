"""
Session management for Janito Chat CLI.
Defines ChatSession and ChatShellState classes.
"""
import types
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
    def __init__(self, console, provider_instance=None, llm_driver_config=None, role=None, args=None):
        self.console = console
        self.user_input_history = UserInputHistory()
        self.input_dicts = self.user_input_history.load()
        self.mem_history = InMemoryHistory()
        for item in self.input_dicts:
            if isinstance(item, dict) and "input" in item:
                self.mem_history.append_string(item["input"])
        self.provider_instance = provider_instance
        self.llm_driver_config = llm_driver_config
        driver = provider_instance.get_driver_for_model(config=llm_driver_config.to_dict())
        from janito.agent.setup_agent import setup_agent
        agent = setup_agent(provider_instance, llm_driver_config, role=role)
        self.shell_state = ChatShellState(self.mem_history, [])
        self.shell_state.agent = agent
        self.agent = agent
        from janito.perf_singleton import performance_collector
        self.performance_collector = performance_collector
        self.key_bindings = KeyBindingsFactory.create()

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
        from prompt_toolkit.application import get_app
        # Use prompt_toolkit application timer for periodic refresh
        termweb_queue = None
        if hasattr(self, 'termweb_support') and self.termweb_support:
            if 'termweb_queue' in locals():
                termweb_queue = locals()['termweb_queue']
        def timer_refresh():
            try:
                if termweb_queue and getattr(self.shell_state, 'termweb_status', None) == 'starting':
                    try:
                        res = termweb_queue.get(timeout=0.01)
                        termweb_proc, started, termweb_stdout_path, termweb_stderr_path, termweb_port = res
                        self.shell_state.termweb_port = termweb_port if started else None
                        self.shell_state.termweb_stdout_path = termweb_stdout_path
                        self.shell_state.termweb_stderr_path = termweb_stderr_path
                        self.shell_state.termweb_status = 'online' if started else 'offline'
                        print(f"[PERIODIC_REFRESH] Got result from startup queue. New status: {self.shell_state.termweb_status}")
                    except Exception:
                        pass
                app = get_app(return_none=True)
                if app:
                    app.invalidate()
            except Exception:
                pass
        # Register the timer after application is initialized, see after session below

        session = PromptSession(
            style=chat_shell_style,
            completer=ShellCommandCompleter(),
            history=self.mem_history,
            editing_mode=EditingMode.EMACS,
            key_bindings=self.key_bindings,
            bottom_toolbar=lambda: get_toolbar_func(
                self.performance_collector, msg_count, self.shell_state
            )(),
        )
        self.console.print("[bold green]Type /help for commands. Type /exit or press Ctrl+C to quit.[/bold green]")
        msg_count = 0
        timer_started = False
        while True:
            # Register timer after first session.prompt(), when Application is definitely available
            if not timer_started:
                from prompt_toolkit.application import get_app
                app = get_app()
                if hasattr(app, 'create_timer'):
                    app.create_timer(0.5, timer_refresh, repeat=True)
                    timer_started = True

            # Support injected input from commands like /multi
            injected = getattr(self.shell_state, 'injected_input', None)
            if injected is not None:
                cmd_input = injected
                self.shell_state.injected_input = None
            else:
                try:
                    cmd_input = session.prompt(HTML("<inputline>💬 </inputline>"))
                except (KeyboardInterrupt, EOFError):
                    self.console.print("\n[bold yellow]Exiting chat. Goodbye![/bold yellow]")
                    break
            cmd_input = cmd_input.strip()
            if not cmd_input:
                continue
            if cmd_input.lower() in ("/exit", ":q", ":quit"):
                self.console.print("[bold yellow]Exiting chat. Goodbye![/bold yellow]")
                should_refresh = False
                refresh_thread.join(timeout=1)
                break
            if cmd_input.lower() in ("/exit", ":q", ":quit"):
                self.console.print("[bold yellow]Exiting chat. Goodbye![/bold yellow]")
                should_refresh = False
                refresh_thread.join(timeout=1)
                break
            if cmd_input.startswith("/"):
                handle_command(cmd_input, shell_state=self.shell_state)
                continue
            # Save input to history
            self.user_input_history.append(cmd_input)
            # Send input to agent and print response
            try:
                # Use GenericPromptHandler for unified prompt handling
                from janito.cli.prompt_core import PromptHandler as GenericPromptHandler
                if not hasattr(self, '_prompt_handler'):
                    # Create once and reuse
                    self._prompt_handler = GenericPromptHandler(
                        args=None,  # No CLI args in chat mode
                        conversation_history=self.shell_state.conversation_history,
                        provider_instance=self.provider_instance
                    )
                    self._prompt_handler.agent = self.agent
                self._prompt_handler.run_prompt(cmd_input)
                msg_count += 1
            except Exception as exc:
                self.console.print(f"[red]Exception in agent: {exc}[/red]")
                import traceback
                self.console.print(traceback.format_exc())
