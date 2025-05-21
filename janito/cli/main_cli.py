import argparse
import enum
from janito.llm.driver_config import LLMDriverConfig

# Enum for command type
class RunMode(enum.Enum):
    GET = "get"
    SET = "set"
    RUN = "run"

# Centralized argument definitions: (argnames, kwargs)
ARG_DEFINITIONS = [
    (["--version"],          {"action": "version", "version": "%(prog)s 1.0"}),
    (["--list-tools"],       {"action": "store_true", "help": "List all registered tools"}),
    (["--show-config"],      {"action": "store_true", "help": "Show the current config"}),
    (["--list-providers"],   {"action": "store_true", "help": "List supported LLM providers"}),
    (["-l", "--list-models"],{"action": "store_true", "help": "List all supported models"}),
    (["--set-api-key"],      {"metavar": "API_KEY", "help": "Set API key for the provider"}),
    (["--set"],              {"metavar": "[PROVIDER_NAME.]KEY=VALUE", "help": "Set a config key"}),
    (["-s", "--system"],    {"metavar": "SYSTEM_PROMPT", "help": "Set a system prompt"}),
    (["-r", "--role"],      {"metavar": "ROLE", "help": "Set the role for the agent"}),
    (["-p", "--provider"],   {"metavar": "PROVIDER", "help": "Select the provider"}),
    (["-m", "--model"],      {"metavar": "MODEL", "help": "Select the model"}),
    (["-t", "--temperature"], {"type": float, "default": None, "help": "Set the temperature"}),
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
            return RunMode.SET
        if any(getattr(self.args, k, None) for k in GETTER_KEYS):
            return RunMode.GET
        return RunMode.RUN

    def handle_setter(self, config_mgr=None):
        set_api_key_handled = self._handle_set_api_key(config_mgr)
        if set_api_key_handled:
            return
        set_handled = self._handle_set(config_mgr)
        if set_handled:
            return

    def _handle_set_api_key(self, config_mgr=None):
        from janito.cli.cli_commands.set_api_key import handle_set_api_key
        if getattr(self.args, "set_api_key", None):
            print(f'[CLI-DEBUG] Invoking setter func for arg: set_api_key with value: {getattr(self.args, "set_api_key")})')
            handle_set_api_key(self.args, config_mgr) if config_mgr else None
            return True
        return False

    def _handle_set(self, config_mgr=None):
        from janito.provider_config import set_default_provider
        set_arg = getattr(self.args, 'set', None)
        if not set_arg:
            return False
        try:
            if '=' not in set_arg:
                print("Error: --set requires KEY=VALUE (e.g., --set default_provider=provider_name).")
                return True
            key, value = set_arg.split('=', 1)
            key, value = key.strip(), value.strip()
            if key == 'default_provider':
                return self._handle_set_default_provider(value, set_default_provider)
            elif '.default_model' in key:
                return self._handle_set_default_model(key, value)
            else:
                print(f"Error: Unknown config key '{key}'. Supported: default_provider, <provider>.default_model")
                return True
        except Exception as e:
            print(f"Error parsing --set value: {e}")
            return True

    def _handle_set_default_provider(self, value, set_default_provider):
        from janito.provider_registry import ProviderRegistry
        try:
            supported = ProviderRegistry().get_provider(value)
        except Exception:
            print(f"Error: Provider '{value}' is not supported. Run '--list-providers' to see the supported list.")
            return True
        set_default_provider(value)
        print(f"Default provider set to '{value}'.")
        return True

    def _handle_set_default_model(self, key, value):
        provider_name, suffix = key.split('.', 1)
        if suffix != "default_model":
            print(f"Error: Only <provider>.default_model is supported for provider-specific model override. Not: '{key}'")
            return True
        from janito.provider_registry import ProviderRegistry
        try:
            provider_cls = ProviderRegistry().get_provider(provider_name)
            provider_instance = provider_cls()
        except Exception:
            print(f"Error: Provider '{provider_name}' is not supported. Run '--list-providers' to see the supported list.")
            return True
        model_info = provider_instance.get_model_info(value)
        if not model_info:
            print(f"Error: Model '{value}' is not defined for provider '{provider_name}'. Run '-p {provider_name} -l' to see models.")
            return True
        from janito.config import config as global_config
        global_config.set_provider_config(provider_name, "default_model", value)
        print(f"Default model for provider '{provider_name}' set to '{value}'.")
        return True

    def handle_getter(self, config_mgr=None):
        from janito.cli.cli_commands.list_providers import handle_list_providers
        from janito.cli.cli_commands.list_models import handle_list_models
        from janito.cli.cli_commands.list_tools import handle_list_tools
        from janito.cli.cli_commands.show_config import handle_show_config
        from functools import partial
        
        provider_instance = None
        if getattr(self.args, 'list_models', False):
            provider = getattr(self.args, 'provider', None)
            if not provider:
                print("Error: No provider selected. Please set a provider using '-p PROVIDER', '--set default_provider=provider_name', or configure a default provider.")
                return
            from janito.provider_registry import ProviderRegistry
            provider_instance = ProviderRegistry().get_instance(provider)

        from janito.cli.cli_commands.list_models import handle_list_models
        GETTER_DISPATCH = {
            "list_providers": partial(handle_list_providers, self.args),
            "list_models": partial(handle_list_models, self.args, provider_instance),
            "list_tools": partial(handle_list_tools, self.args),
            "show_config": partial(handle_show_config, self.args),
        }
        for arg in GETTER_KEYS:
            if getattr(self.args, arg, False) and arg in GETTER_DISPATCH:
                return GETTER_DISPATCH[arg]()

    def handle_runner(self, provider, llm_driver_config, agent_role):
        from janito.provider_registry import ProviderRegistry
        from janito.cli.verbose_output import print_verbose_info
        provider_instance = ProviderRegistry().get_instance(provider, llm_driver_config)
        
        # Pass the role attribute to agent creation logic as needed
        # If further down the stack (e.g., setup_agent or handler) supports role, it should be wired there
        mode = self.get_prompt_mode()
        if getattr(self.args, 'verbose', False):
            print_verbose_info("Active LLMDriverConfig (after provider)", llm_driver_config, style="green")
            print_verbose_info("Agent role", agent_role, style="green")
        if mode == "single_shot":
            from janito.cli.single_shot_mode.handler import PromptHandler as SingleShotPromptHandler
            handler = SingleShotPromptHandler(self.args, provider_instance, llm_driver_config, role=agent_role)
            handler.handle()
        else:
            from janito.cli.chat_mode.session import ChatSession
            from rich.console import Console
            console = Console()
            session = ChatSession(console, provider_instance, llm_driver_config, role=agent_role)
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

    def _setup_event_logger_if_needed(self):
        if getattr(self.args, 'event_log', False):
            print("[EventLog] Setting up event logger with system bus...")
            self.setup_event_logger()
            from janito.event_bus import event_bus
            def event_logger_handler(event):
                print(f"[EventLog] {event.__class__.__name__} | {getattr(event, 'category', '')} | {event}")
            from janito.event_bus.event import Event
            event_bus.subscribe(Event, event_logger_handler)

    def _inject_debug_event_bus_if_needed(self):
        if getattr(self.args, 'event_debug', False):
            from janito.event_bus import event_bus
            orig_publish = event_bus.publish
            def debug_publish(event):
                print(f"[EventBus][DEBUG] Publishing event: {event.__class__.__name__} | {getattr(event, 'category', '')} | {event}")
                return orig_publish(event)
            event_bus.publish = debug_publish

    def _prepare_llm_driver_config(self, modifiers):
        provider = getattr(self.args, 'provider', None)
        if provider is None:
            from janito.provider_config import get_default_provider
            provider = get_default_provider()
            if provider:
                if getattr(self.args, 'verbose', False):
                    from janito.cli.verbose_output import print_verbose_info
                    print_verbose_info("Default provider", provider, style="magenta", align_content=True)
            else:
                print("Error: No provider selected and no default_provider found in config. Please set a provider using '-p PROVIDER', '--set default_provider=provider_name', or configure a default provider.")
                return None, None
        model = getattr(self.args, 'model', None)
        driver_config_data = {"model": model}
        for field in LLMDriverConfig.__dataclass_fields__:
            if field in modifiers and field != "model" and field in LLMDriverConfig.__dataclass_fields__:
                driver_config_data[field] = modifiers[field]
        llm_driver_config = LLMDriverConfig(**driver_config_data)
        # Role is not part of LLMDriverConfig, set it separately for agent
        agent_role = modifiers.get("role", "software developer")
        return provider, llm_driver_config, agent_role
        return provider, llm_driver_config

    def run(self):
        modifiers = self.collect_modifiers()
        if getattr(self.args, 'verbose', False):
            from janito.cli.verbose_output import print_verbose_info
            print_verbose_info("Modifiers collected", modifiers, style="blue")
        self._setup_event_logger_if_needed()
        self._inject_debug_event_bus_if_needed()

        run_mode = self.classify()
        if run_mode == RunMode.GET and (getattr(self.args, 'list_providers', False) or getattr(self.args, 'list_tools', False)):
            if getattr(self.args, 'verbose', False):
                from janito.cli.verbose_output import print_verbose_info
                print_verbose_info("Validated provider/model", f"Provider: {getattr(self.args, 'provider', None)} | Model: {getattr(self.args, 'model', None)}", style="blue")
            self.handle_getter()
            return
        provider, llm_driver_config, agent_role = self._prepare_llm_driver_config(modifiers)
        if llm_driver_config is None:
            return
        if getattr(self.args, 'verbose', False):
            from janito.cli.verbose_output import print_verbose_info
            print_verbose_info("LLMDriverConfig", llm_driver_config, style="cyan")
            print_verbose_info("Dispatch branch", run_mode, style="cyan", align_content=True)
        if run_mode == RunMode.RUN:
            if getattr(self.args, 'verbose', False):
                from janito.cli.verbose_output import print_verbose_info
                print_verbose_info("Run mode", self.get_prompt_mode(), style="cyan", align_content=True)
            self.handle_runner(provider, llm_driver_config, agent_role)
        elif run_mode == RunMode.SET:
            self.handle_setter()
        elif run_mode == RunMode.GET:
            self.handle_getter()

if __name__ == "__main__":
    cli = JanitoCLI()
    cli.run()
