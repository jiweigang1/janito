import argparse
import enum
from janito.cli.core.setters import handle_api_key_set, handle_set
from janito.cli.core.getters import handle_getter
from janito.cli.core.runner import prepare_llm_driver_config, handle_runner, get_prompt_mode
from janito.cli.core.event_logger import setup_event_logger_if_needed, inject_debug_event_bus_if_needed

definition = [
    (['--verbose-api'], {"action": "store_true", "help": "Print API calls and responses of LLM driver APIs for debugging/tracing."}),
    (['-z', '--zero'], {"action": "store_true", "help": "IDE zero mode: disables system prompt & all tools for raw LLM interaction"}),
    (["--unset"], {"metavar": "KEY", "help": "Unset (remove) a config key"}),
    (['--version'], {"action": "version", "version": None}),
    (['--list-tools'], {"action": "store_true", "help": "List all registered tools"}),
    (['--show-config'], {"action": "store_true", "help": "Show the current config"}),
    (['--list-providers'], {"action": "store_true", "help": "List supported LLM providers"}),
    (['-l', '--list-models'], {"action": "store_true", "help": "List all supported models"}),
    (['--set-api-key'], {"metavar": "API_KEY", "help": "Set API key for the provider"}),
    (['--set'], {"metavar": "[PROVIDER_NAME.]KEY=VALUE", "help": "Set a config key"}),
    (['-s', '--system'], {"metavar": "SYSTEM_PROMPT", "help": "Set a system prompt"}),
    (['-r', '--role'], {"metavar": "ROLE", "help": "Set the role for the agent"}),
    (['-p', '--provider'], {"metavar": "PROVIDER", "help": "Select the provider"}),
    (['-m', '--model'], {"metavar": "MODEL", "help": "Select the model"}),
    (['-t', '--temperature'], {"type": float, "default": None, "help": "Set the temperature"}),
    (['-v', '--verbose'], {"action": "store_true", "help": "Print extra information before answering"}),
    (['-R', '--raw'], {"action": "store_true", "help": "Print the raw JSON response from the OpenAI API (if applicable)"}),
    (['--no-termweb'], {"action": "store_true", "help": "Disable the builtin lightweight web file viewer for terminal links (enabled by default)"}),
    (['--termweb-port'], {"type": int, "default": 8088, "help": "Port for the termweb server (default: 8088)"}),
    (["user_prompt"], {"nargs": argparse.REMAINDER, "help": "Prompt to submit"}),
    (['-e', '--event-log'], {"action": "store_true", "help": "Enable event logging to the system bus"}),
    (["--event-debug"], {"action": "store_true", "help": "Print debug info on event subscribe/submit methods"})
]

MODIFIER_KEYS = ["provider", "model", "role", "system", "temperature", "verbose", "raw", "no_termweb", "termweb_port", "verbose_api"]
SETTER_KEYS = ["set", "set_provider", "set_api_key", "unset"]
GETTER_KEYS = ["show_config", "list_providers", "list_models", "list_tools"]

class RunMode(enum.Enum):
    GET = "get"
    SET = "set"
    RUN = "run"

class JanitoCLI:
    def __init__(self):
        import janito.tools
        self.parser = argparse.ArgumentParser(description="Janito CLI - A tool for running LLM-powered workflows from the command line."\
                                               "\n\nExample usage: janito -p openai -m gpt-3.5-turbo 'Your prompt here'\n\n"\
                                               "Use -m or --model to set the model for the session.")
        self._define_args()
        self.args = self.parser.parse_args()
        from janito.cli.rich_terminal_reporter import RichTerminalReporter
        self.rich_reporter = RichTerminalReporter(raw_mode=getattr(self.args, 'raw', False))

    def _define_args(self):
        for argnames, argkwargs in definition:
            # Patch version argument dynamically with real version
            if '--version' in argnames:
                from janito import __version__ as janito_version
                argkwargs['version'] = f"Janito {janito_version}"
            self.parser.add_argument(*argnames, **argkwargs)

    def collect_modifiers(self):
        return {k: getattr(self.args, k) for k in MODIFIER_KEYS if getattr(self.args, k, None) is not None}

    def classify(self):
        if any(getattr(self.args, k, None) for k in SETTER_KEYS):
            return RunMode.SET
        if any(getattr(self.args, k, None) for k in GETTER_KEYS):
            return RunMode.GET
        return RunMode.RUN

    def run(self):
        run_mode = self.classify()
        if run_mode == RunMode.SET:
            if self._run_set_mode():
                return
        # Special handling: provider is not required for list_providers, list_tools, show_config
        if run_mode == RunMode.GET and (getattr(self.args, 'list_providers', False)
                                        or getattr(self.args, 'list_tools', False)
                                        or getattr(self.args, 'show_config', False)):
            self._maybe_print_verbose_provider_model()
            handle_getter(self.args)
            return
        provider = self._get_provider_or_default()
        if provider is None:
            print("Error: No provider selected and no provider found in config. Please set a provider using '-p PROVIDER', '--set provider=name', or configure a provider.")
            return
        modifiers = self.collect_modifiers()
        self._maybe_print_verbose_modifiers(modifiers)
        setup_event_logger_if_needed(self.args)
        inject_debug_event_bus_if_needed(self.args)
        provider, llm_driver_config, agent_role = prepare_llm_driver_config(self.args, modifiers)
        if provider is None or llm_driver_config is None:
            return
        self._maybe_print_verbose_llm_config(llm_driver_config, run_mode)
        if run_mode == RunMode.RUN:
            self._maybe_print_verbose_run_mode()
            handle_runner(self.args, provider, llm_driver_config, agent_role)
        elif run_mode == RunMode.GET:
            handle_getter(self.args)

    def _run_set_mode(self):
        if handle_api_key_set(self.args):
            return True
        if handle_set(self.args):
            return True
        from janito.cli.core.unsetters import handle_unset
        if handle_unset(self.args):
            return True
        return False

    def _get_provider_or_default(self):
        provider = getattr(self.args, 'provider', None)
        if provider is None:
            from janito.provider_config import get_config_provider
            provider = get_config_provider()
        return provider

    def _maybe_print_verbose_modifiers(self, modifiers):
        if getattr(self.args, 'verbose', False):
            from janito.cli.verbose_output import print_verbose_info
            print_verbose_info("Modifiers collected", modifiers, style="blue")

    def _maybe_print_verbose_provider_model(self):
        if getattr(self.args, 'verbose', False):
            from janito.cli.verbose_output import print_verbose_info
            print_verbose_info(
                "Validated provider/model",
                f"Provider: {getattr(self.args, 'provider', None)} | Model: {getattr(self.args, 'model', None)}",
                style="blue",
            )

    def _maybe_print_verbose_llm_config(self, llm_driver_config, run_mode):
        if getattr(self.args, 'verbose', False):
            from janito.cli.verbose_output import print_verbose_info
            print_verbose_info("LLMDriverConfig", llm_driver_config, style="cyan")
            print_verbose_info("Dispatch branch", run_mode, style="cyan", align_content=True)

    def _maybe_print_verbose_run_mode(self):
        if getattr(self.args, 'verbose', False):
            from janito.cli.verbose_output import print_verbose_info
            print_verbose_info("Run mode", get_prompt_mode(self.args), style="cyan", align_content=True)

if __name__ == "__main__":
    cli = JanitoCLI()
    cli.run()
