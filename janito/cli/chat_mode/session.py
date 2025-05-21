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
from janito.cli.chat_mode.bindings import KeyBindingsFactory
from janito.cli.chat_mode.shell.commands import handle_command

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
    def __init__(self, console, provider_instance, llm_driver_config):
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
        agent = provider_instance.create_agent(
            agent_name=getattr(llm_driver_config, 'role', None),
            config=llm_driver_config.to_dict(),
            system_prompt=getattr(llm_driver_config, 'system', None),
            temperature=getattr(llm_driver_config, 'temperature', None),
        )
        self.shell_state = ChatShellState(self.mem_history, [])
        self.shell_state.agent = agent
        self.agent = agent
        from janito.perf_singleton import performance_collector
        self.performance_collector = performance_collector
        self.key_bindings = KeyBindingsFactory.create()

    def run(self):
        session = PromptSession(
            history=self.mem_history,
            editing_mode=EditingMode.EMACS,
            key_bindings=self.key_bindings,
            bottom_toolbar=get_toolbar_func(self.performance_collector, msg_count=0, agent=self.agent),
        )
        self.console.print("[bold green]Type /help for commands. Type /exit or press Ctrl+C to quit.[/bold green]")
        msg_count = 0
        while True:
            try:
                cmd_input = session.prompt(HTML("<b>janito</b> > "))
            except (KeyboardInterrupt, EOFError):
                self.console.print("\n[bold yellow]Exiting chat. Goodbye![/bold yellow]")
                break
            cmd_input = cmd_input.strip()
            if not cmd_input:
                continue
            if cmd_input.lower() in ("/exit", ":q", ":quit"):
                self.console.print("[bold yellow]Exiting chat. Goodbye![/bold yellow]")
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
