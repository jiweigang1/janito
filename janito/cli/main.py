"""
janito.cli: Command Line Interface for janito

Provides commands for managing API keys and interacting with LLM providers.
"""
import argparse
import sys
from janito.version import __version__ as VERSION
from janito.provider_registry import list_providers, select_provider
from janito.cli.one_shot_run.handler import PromptHandler
from janito.provider_config import ProviderConfigManager
from janito.cli.runtime_config import runtime_config
from rich.console import Console
from rich.pretty import Pretty

def log_event_to_console(event):
    from janito.console import shared_console
    shared_console.print(f"[EVENT] [bold cyan]{event.__class__.__name__}[/]:", Pretty(event.__dict__, expand_all=True))

def handle_list_tools():
    from janito.tool_registry import ToolRegistry
    import janito.tools  # Ensure all tools are registered
    registry = ToolRegistry()
    tools = registry.list_tools()
    if tools:
        print("Registered tools:")
        for tool in tools:
            print(f"- {tool}")
    else:
        print("No tools registered.")
    sys.exit(0)

def handle_set_api_key(args, mgr):
    provider, api_key = args.set_api_key
    mgr.set_api_key(provider, api_key)
    print(f"API key set for provider '{provider}'.")

def handle_set_provider(args, mgr):
    mgr.set_default_provider(args.set_provider)
    print(f"Current provider set to '{args.set_provider}' in {mgr.get_config_path()}.")

def handle_set_config(args, mgr):
    provider, key, value = args.set_config
    mgr.set_provider_config(provider, key, value)
    print(f"Set config for provider '{provider}': {key} = {value}")

def handle_list_providers():
    list_providers()

def handle_user_prompt(args):
    prompt = ' '.join(args.user_prompt).strip()
    if not prompt:
        return False
    setattr(args, 'user_prompt', prompt)
    if args.event_log:
        from janito.event_bus.bus import event_bus
        from janito.event_bus.event import Event
        # Subscribe to all events (catch-all)
        event_bus.subscribe(Event, log_event_to_console, priority=0)
    result = PromptHandler(args).handle()
    if args.raw and result is not None:
        print(result)
    return True

def set_default_system_prompt(args):
    import os
    import sys
    if not getattr(args, 'system', None):
        default_system_prompt = os.path.join(
            os.path.dirname(__file__),
            '../agent/templates/profiles/system_prompt_template_base.txt.j2'
        )
        if os.path.isfile(default_system_prompt):
            args.system = default_system_prompt
        else:
            # Try to find it as an installed package resource
            try:
                import importlib.resources as pkg_resources
                with pkg_resources.path('janito.agent.templates.profiles', 'system_prompt_template_base.txt.j2') as pkg_path:
                    if pkg_path.is_file():
                        args.system = str(pkg_path)
                    else:
                        raise FileNotFoundError
            except Exception:
                print(f"Error: Default system prompt template not found in source or installed package.", file=sys.stderr)
                sys.exit(1)

def validate_model_for_provider(provider_name, model_name):
    """
    Check if the given model is available for the provider.
    Returns True if available, False otherwise.
    """
    try:
        from janito.providers.registry import LLMProviderRegistry
        provider_cls = LLMProviderRegistry.get(provider_name)
        # Try to call list_models if implemented
        if hasattr(provider_cls, 'list_models'):
            available_models = provider_cls.list_models()
            # Expecting a list of dicts with 'name' field
            available_names = [m["name"] for m in available_models if isinstance(m, dict) and "name" in m]
            if model_name in available_names:
                return True
            else:
                print(f"Error: Model '{model_name}' is not available for provider '{provider_name}'.")
                print(f"Available models: {', '.join(available_names)}")
                return False
        else:
            print(f"Warning: Model validation is not supported for provider '{provider_name}'. Proceeding without validation.")
            return True
    except Exception as e:
        print(f"Error validating model for provider '{provider_name}': {e}")
        return False

def handle_set_model(args):
    provider_name = getattr(args, 'provider', None)
    if not provider_name:
        provider_name = ProviderConfigManager().get_default_provider()
    if not provider_name:
        print("Error: Provider must be specified with --provider or set as default before setting a model.")
        sys.exit(1)
    if not validate_model_for_provider(provider_name, args.set_model):
        sys.exit(1)
    ProviderConfigManager().set_provider_config(provider_name, "model", args.set_model)
    print(f"Default model for provider '{provider_name}' set to '{args.set_model}' in {{ProviderConfigManager().get_config_path()}}.")
    sys.exit(0)

def handle_list_models(args):
    provider_name = getattr(args, 'provider', None)
    if not provider_name:
        provider_name = ProviderConfigManager().get_default_provider()
    if not provider_name:
        print("Error: Provider must be specified with --provider or set as default before listing models.")
        sys.exit(1)
    try:
        from janito.providers.registry import LLMProviderRegistry
        provider_cls = LLMProviderRegistry.get(provider_name)
        if hasattr(provider_cls, 'list_models'):
            models = provider_cls.list_models()
            # If models is a list of dicts with detailed info, print as table
            if models and isinstance(models[0], dict):
                from rich.table import Table
                from rich.console import Console
                headers = ["name", "open", "context", "max_input", "max_cot", "max_response", "thinking_supported"]
                display_headers = ["Model Name", "Vendor", "context", "max_input", "max_cot", "max_response", "Thinking"]
                table = Table(title=f"Supported models for provider '{provider_name}'")
                for i, h in enumerate(display_headers):
                    justify = "right" if i == 0 else "center"
                    table.add_column(h, style="bold", justify=justify)
                def format_k(val):
                    try:
                        n = int(val)
                        if n >= 1000:
                            return f"{n // 1000}k"
                        return str(n)
                    except Exception:
                        return str(val)

                num_fields = {"context", "max_input", "max_cot", "max_response"}
                for m in models:
                    row = [str(m.get("name", ""))]
                    for h in headers[1:]:
                        v = m.get(h, "")
                        if h in num_fields and v not in ("", "N/A"):
                            if h in ("context", "max_input") and isinstance(v, (list, tuple)) and len(v) == 2:
                                row.append(f"{format_k(v[0])} / {format_k(v[1])}")
                            else:
                                row.append(format_k(v))
                        elif h == "open":
                            row.append("Open" if v is True or v == "Open" else "Locked")
                        elif h == "thinking_supported":
                            row.append("✔" if v is True or v == "True" else "")
                        else:
                            row.append(str(v))
                    table.add_row(*row)
                console = Console()
                console.print(table)
            else:
                print(f"Supported models for provider '{provider_name}':")
                for m in models:
                    print(f"- {m}")
        else:
            print(f"Provider '{provider_name}' does not support model listing.")
    except Exception as e:
        print(f"Error listing models for provider '{provider_name}': {e}")
    sys.exit(0)

def handle_model_selection(args):
    if getattr(args, 'model', None):
        provider_name = getattr(args, 'provider', None)
        if not provider_name:
            provider_name = ProviderConfigManager().get_default_provider()
        if not provider_name:
            print("Error: Provider must be specified with --provider or set as default before selecting a model.")
            sys.exit(1)
        if not validate_model_for_provider(provider_name, args.model):
            sys.exit(1)
        runtime_config.set('model', args.model)

def dispatch_command(args, mgr, parser):
    if args.list_tools:
        handle_list_tools()
    elif args.set_api_key:
        handle_set_api_key(args, mgr)
    elif args.set_provider:
        handle_set_provider(args, mgr)
    elif args.set_config:
        handle_set_config(args, mgr)
    elif args.list_providers:
        handle_list_providers()
    elif args.user_prompt:
        if not handle_user_prompt(args):
            parser.print_help()
    else:
        # If no user prompt is provided, start the chat shell
        from janito.cli.chat_shell import main as chat_shell_main
        chat_shell_main()

def main():
    """
    Entry point for the janito CLI.
    Parses command-line arguments and executes the corresponding actions.
    """
    parser = argparse.ArgumentParser(description="Janito CLI")
    parser.add_argument('--version', action='version', version=f'%(prog)s {VERSION}')
    parser.add_argument('--list-tools', action='store_true', help='List all registered tools')
    parser.add_argument('--list-providers', action='store_true', help='List all supported LLM providers')
    parser.add_argument('-l', '--list-models', action='store_true', help='List all supported models for the current or selected provider')
    parser.add_argument('--set-api-key', nargs=2, metavar=('PROVIDER', 'API_KEY'), help='Set API key for a provider')
    parser.add_argument('--set-provider', metavar='PROVIDER', help='Set the current LLM provider (stores in ~/janito/config.json)')
    parser.add_argument('--set-config', nargs=3, metavar=('PROVIDER', 'KEY', 'VALUE'), help='Set a provider-specific config value')
    parser.add_argument('--set-model', metavar='MODEL', help='Set the default model for the current or selected provider (stores in ~/janito/config.json)')
    parser.add_argument('-s', '--system', metavar='SYSTEM_PROMPT', help='Set a system prompt for the LLM agent')
    parser.add_argument('-p', '--provider', metavar='PROVIDER', help='Select the LLM provider (overrides config)')
    parser.add_argument('-m', '--model', metavar='MODEL', help='Select the model for the provider (overrides config)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Print extra information before answering')
    parser.add_argument('-r', '--raw', action='store_true', help='Print the raw JSON response from the OpenAI API (if applicable)')
    parser.add_argument('-e', '--event-log', action='store_true', help='Log events to the console as they are published')
    parser.add_argument('user_prompt', nargs=argparse.REMAINDER, help='Prompt to submit (if no other command is used)')

    args = parser.parse_args()

    set_default_system_prompt(args)

    if getattr(args, 'set_model', None):
        handle_set_model(args)

    if getattr(args, 'list_models', False):
        handle_list_models(args)

    handle_model_selection(args)

    from janito.rich_terminal_reporter import RichTerminalReporter
    _rich_ui_manager = RichTerminalReporter(raw_mode=args.raw)

    mgr = ProviderConfigManager()
    dispatch_command(args, mgr, parser)

if __name__ == "__main__":
    main()
