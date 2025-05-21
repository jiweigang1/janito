import argparse
from janito.llm.driver_config import LLMDriverConfig
from janito.cli.provider_setup import setup_provider
from janito.cli.classic_cli_validate import validate_modifiers

# Centralized argument definitions: (argnames, kwargs)
ARG_DEFINITIONS = [
    (["--version"],          {"action": "version", "version": "%(prog)s 1.0"}),
    (["--list-tools"],       {"action": "store_true", "help": "List all registered tools"}),
    (["--show-config"],      {"action": "store_true", "help": "Show the current config"}),
    (["--list-providers"],   {"action": "store_true", "help": "List supported LLM providers"}),
    (["-l", "--list-models"],{"action": "store_true", "help": "List all supported models"}),
    (["--set-api-key"],      {"metavar": "API_KEY", "help": "Set API key for the provider"}),
    (["--set-provider"],     {"metavar": "PROVIDER", "help": "Set the LLM provider"}),
    (["--set"],              {"metavar": "[PROVIDER_NAME.]KEY=VALUE", "help": "Set a config key"}),
    (["-s", "--system"],     {"metavar": "SYSTEM_PROMPT", "help": "Set a system prompt"}),
    (["-r", "--role"],       {"metavar": "ROLE", "help": "Set the role for the agent"}),
    (["-p", "--provider"],   {"metavar": "PROVIDER", "help": "Select the provider"}),
    (["-m", "--model"],      {"metavar": "MODEL", "help": "Select the model"}),
    (["-t", "--temperature"],{"type": float, "default": None, "help": "Set the temperature"}),
    (["-v", "--verbose"],    {"action": "store_true", "help": "Print extra information before answering"}),
    (["-R", "--raw"],        {"action": "store_true", "help": "Print the raw JSON response from the OpenAI API (if applicable)"}),
    (["--no-termweb"],       {"action": "store_true", "help": "Disable the builtin lightweight web file viewer for terminal links (enabled by default)"}),
    (["--termweb-port"],     {"type": int, "default": 8088, "help": "Port for the termweb server (default: 8088)"}),
    (["user_prompt"],        {"nargs": argparse.REMAINDER, "help": "Prompt to submit"}),
    (["-e", "--event-log"],       {"action": "store_true", "help": "Enable event logging to the system bus"}),
    (["--event-debug"],      {"action": "store_true", "help": "Print debug info on event subscribe/submit methods"})
]

MODIFIER_KEYS = [
    "provider", "model", "role", "system", "temperature",
    "verbose", "raw", "no_termweb", "termweb_port"
]
SETTER_KEYS   = ["set", "set_provider", "set_api_key"]
GETTER_KEYS   = ["show_config", "list_providers", "list_models", "list_tools"]


class JanitoCLI:
    def __init__(self):
        import janito.tools  # Ensure all tools are registered at CLI startup
        self.parser = argparse.ArgumentParser(description="Janito CLI")
        self._define_args()
        self.args = self.parser.parse_args()
        from janito.cli.rich_terminal_reporter import RichTerminalReporter
        self.rich_reporter = RichTerminalReporter(raw_mode=getattr(self.args, 'raw', False))

    def _define_args(self):
        for argnames, argkwargs in ARG_DEFINITIONS:
            self.parser.add_argument(*argnames, **argkwargs)

    def collect_modifiers(self):
        return {k: getattr(self.args, k) for k in MODIFIER_KEYS if getattr(self.args, k, None) is not None}

    def classify(self):
        if any(getattr(self.args, k, None) for k in SETTER_KEYS):
            return 'setter'
        if any(getattr(self.args, k, None) for k in GETTER_KEYS):
            return 'getter'
        return 'runner'

    def handle_setter(self, config_mgr=None):
        from janito.cli.cli_commands.set_api_key import handle_set_api_key
        from janito.cli.cli_commands.set_provider import handle_set_provider
        from janito.cli.cli_commands.set_provider_kv import handle_set_provider_kv

        SETTER_DISPATCH = {
            "set_api_key": lambda: handle_set_api_key(self.args, config_mgr) if config_mgr else None,
            "set_provider": lambda: handle_set_provider(self.args, config_mgr) if config_mgr else None,
            "set": lambda: handle_set_provider_kv(self.args, config_mgr) if config_mgr else None,
        }
        for arg, func in SETTER_DISPATCH.items():
            if getattr(self.args, arg, None):
                func()
                break

    def handle_getter(self, config_mgr=None):
        from janito.cli.cli_commands.list_providers import handle_list_providers
        from janito.cli.cli_commands.list_models import handle_list_models
        from janito.cli.cli_commands.list_tools import handle_list_tools
        from janito.cli.cli_commands.show_config import handle_show_config
        from functools import partial
        from janito.cli.provider_setup import setup_provider

        provider_instance = None
        if getattr(self.args, 'list_models', False):
            provider_instance = setup_provider(self.args.provider)

        GETTER_DISPATCH = {
            "list_providers": partial(handle_list_providers, self.args),
            "list_models": partial(handle_list_models, self.args, provider_instance),
            "list_tools": partial(handle_list_tools, self.args),
            "show_config": partial(handle_show_config, self.args),
        }
        for arg in GETTER_KEYS:
            if getattr(self.args, arg, False) and arg in GETTER_DISPATCH:
                return GETTER_DISPATCH[arg]()

    def handle_runner(self, provider_instance, llm_driver_config):
        # Ensure rich reporter is set up for event-driven output
        mode = self.get_prompt_mode()
        if mode == "single_shot":
            from janito.cli.single_shot_mode.handler import PromptHandler as SingleShotPromptHandler
            handler = SingleShotPromptHandler(self.args, provider_instance, llm_driver_config)
            handler.handle()
        else:
            from janito.cli.chat_mode.session import ChatSession
            from rich.console import Console
            console = Console()
            session = ChatSession(console, provider_instance, llm_driver_config)
            session.run()

    def get_prompt_mode(self):
        if self.args.user_prompt:
            return 'single_shot'
        else:
            return 'chat_mode'

    class EventLogger:
        def __init__(self, debug=False):
            self.debug = debug
            if self.debug:
                print("[EventLog][DEBUG] EventLogger initialized with debug mode ON")
        def subscribe(self, event_name, callback):
            if self.debug:
                print(f"[EventLog][DEBUG] Subscribed to event: {event_name}")
            # Stub: No real subscription logic
        def submit(self, event_name, payload=None):
            if self.debug:
                print(f"[EventLog][DEBUG] Submitted event: {event_name} with payload: {payload}")
            # Stub: No real submission logic

    def setup_event_logger(self):
        debug = getattr(self.args, 'event_debug', False)
        self.event_logger = self.EventLogger(debug=debug)
        print("[EventLog] Event logger is now active (stub implementation)")

    def run(self):
        modifiers = self.collect_modifiers()
        print("Modifiers collected:", modifiers)
        # Event logger setup
        if getattr(self.args, 'event_log', False):
            print("[EventLog] Setting up event logger with system bus...")
            self.setup_event_logger()
            # Subscribe event logger to event bus
            from janito.event_bus import event_bus
            def event_logger_handler(event):
                print(f"[EventLog] {event.__class__.__name__} | {getattr(event, 'category', '')} | {event}")
            # Subscribe to all events (base Event class)
            from janito.event_bus.event import Event
            event_bus.subscribe(Event, event_logger_handler)

        if getattr(self.args, 'event_debug', False):
            from janito.event_bus import event_bus
            orig_publish = event_bus.publish
            def debug_publish(event):
                print(f"[EventBus][DEBUG] Publishing event: {event.__class__.__name__} | {getattr(event, 'category', '')} | {event}")
                return orig_publish(event)
            event_bus.publish = debug_publish

        provider, model = validate_modifiers(modifiers)
        print(f"Validated provider: {provider}, model: {model}")
        provider_instance = setup_provider(provider)
        driver_config_data = {"model": model}
        for field in LLMDriverConfig.__dataclass_fields__:
            if field in modifiers and field != "model":
                driver_config_data[field] = modifiers[field]
        llm_driver_config = LLMDriverConfig(**driver_config_data)
        print("Constructed LLMDriverConfig:", llm_driver_config)
        classification = self.classify()
        print("Dispatch branch:", classification)
        if classification == 'runner':
            print("Run mode:", self.get_prompt_mode())
            self.handle_runner(provider_instance, llm_driver_config)
        elif classification == 'setter':
            self.handle_setter()
        elif classification == 'getter':
            self.handle_getter()

if __name__ == "__main__":
    cli = JanitoCLI()
    cli.run()
