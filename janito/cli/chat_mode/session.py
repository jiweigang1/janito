"""
Session management for Janito Chat CLI.
Defines ChatSession and ChatShellState classes.
"""
import types
from prompt_toolkit.history import InMemoryHistory
from janito.cli.chat_mode.shell.input_history import UserInputHistory
from janito.cli.agent_utils import build_cli_agent_and_history
from janito.cli.prompt_handler import PromptHandler
from janito.cli.config import config
from janito.cli.chat_mode.toolbar import get_toolbar_func
from janito.cli.chat_mode.bindings import KeyBindingsFactory
from janito.cli.agent_setup import AgentSetup
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit import PromptSession
from janito.cli.chat_mode.toolbar_style import toolbar_style
from prompt_toolkit.enums import EditingMode

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
        self.last_usage_info = {}
        self.last_elapsed = None
        self.main_agent = {}
        self.mode = None
        self.agent = None
        self.main_agent = None
        self.main_enabled = False

class ChatSession:
    def __init__(self, console):
        self.console = console
        self.user_input_history = UserInputHistory()
        self.input_dicts = self.user_input_history.load()
        self.mem_history = InMemoryHistory()
        for item in self.input_dicts:
            if isinstance(item, dict) and "input" in item:
                self.mem_history.append_string(item["input"])
        provider_instance, conversation_history, agent = build_cli_agent_and_history(config)
        self.conversation_history = conversation_history
        self.shell_state = ChatShellState(self.mem_history, self.conversation_history)
        self.handler = PromptHandler(config, conversation_history=self.conversation_history, provider_instance=provider_instance)
        self.shell_state.agent = agent
        self.agent_setup = AgentSetup(self.shell_state, self.conversation_history)
        self.agent_setup.setup_agents(provider_instance)
        self.handler.agent = self.shell_state.agent
        # Toolbar role sync
        current_role = config.get('role') or '<not set>'
        agent = self.shell_state.agent
        if agent and hasattr(agent, "set_template_var"):
            agent.set_template_var("role", current_role)
        from janito.perf_singleton import performance_collector
        self.key_bindings = KeyBindingsFactory.create()
        toolbar_func = get_toolbar_func(
            perf=performance_collector,
            msg_count=len(self.conversation_history.get_history()),
            agent=self.shell_state.agent
        )
        self.session = PromptSession(
            bottom_toolbar=toolbar_func,
            style=toolbar_style,
            editing_mode=EditingMode.VI,
            key_bindings=self.key_bindings,
            history=self.mem_history,
        )
    def run(self):
        from janito.cli.chat_mode.shell.commands import handle_command
        while True:
            try:
                user_prompt = self.session.prompt(HTML("<inputline>💬 </inputline>"), multiline=False)
            except (EOFError, KeyboardInterrupt):
                self.console.print("\n[bold red]Exiting chat mode.[/bold red]")
                break
            cmd_input = user_prompt.strip()
            if not cmd_input:
                continue
            if cmd_input.startswith("/") or cmd_input.lower() in {"exit", ":q", "quit"}:
                prev_mode = getattr(self.shell_state, 'mode', 'main')
                result = handle_command(cmd_input, shell_state=self.shell_state)
                if prev_mode != getattr(self.shell_state, 'mode', prev_mode):
                    self.handler.agent = self.shell_state.agent
                    self.toolbar_renderer.shell_state = self.shell_state
                    self.session = PromptSession(
                        bottom_toolbar=self.toolbar_renderer.render,
                        style=toolbar_style,
                        editing_mode=EditingMode.VI,
                        key_bindings=self.key_bindings,
                        history=self.mem_history,
                    )
                if result == "exit":
                    break
                continue
            self.user_input_history.append(cmd_input)
            self.handler.agent = self.shell_state.agent
            self.handler.args.user_prompt = cmd_input
            try:
                self.handler.handle_prompt(cmd_input, args=self.handler.args, print_header=False, raw=False)
            except Exception as exc:
                self.console.print(f"[red]Exception in handler.run_prompt: {exc}[/red]")
                import traceback
                self.console.print(traceback.format_exc())
