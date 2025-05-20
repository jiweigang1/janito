"""
janito.cli: Command Line Interface for janito

Provides commands for managing API keys and interacting with LLM providers.
"""
import argparse
import sys
from rich.console import Console
from rich.pretty import Pretty
from janito.version import __version__ as VERSION
from janito.provider_registry import list_providers
from janito.cli.single_shot_mode.handler import PromptHandler
from janito.cli.config import config
from janito.cli.provider_setup import setup_provider

# Singleton provider instance for reuse
_provider_instance = None

def get_provider_instance():
    global _provider_instance
    if _provider_instance is None:
        _provider_instance = setup_provider()
    return _provider_instance

def log_event_to_console(event):
    from janito.cli.console import shared_console
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
    api_key = args.set_api_key
    provider_instance = get_provider_instance()
    try:
        provider = getattr(provider_instance, 'name', None)

        if not provider:
            print("Error: No provider could be determined from setup_provider.")
            return
    except Exception as ex:
        import traceback; traceback.print_exc()
        print(f"[janito EXCEPTION] Exception when getting provider_instance.name: {ex!r}")
        return
    mgr.set_api_key(provider, api_key)
    print(f"API key set for provider '{provider}'.")

def handle_set_provider(args, mgr):
    mgr.set_default_provider(args.set_provider)
    print(f"Current provider set to '{args.set_provider}' in {mgr.get_config_path()}.")

def handle_set_provider_kv(args, mgr):
    # args.set is expected to look like: '[provider[.model].]key=value'
    set_arg = args.set.strip()
    if '=' not in set_arg:
        print("Error: --set requires argument in the form [PROVIDER_NAME[.MODEL].]KEY=VALUE")
        print("Example: --set openai.gpt-3.5-turbo.max_tokens=4096 or --set openai.base_url=https://api... or --set model=gpt-3")
        return
    keypart, value = set_arg.split('=', 1)
    dot_parts = keypart.split('.')
    if len(dot_parts) == 3:
        provider, model, key = dot_parts
    elif len(dot_parts) == 2:
        provider, key = dot_parts
        model = None
    else:
        provider_instance = get_provider_instance()
        provider = getattr(provider_instance, 'name', None)
        if not provider:
            print("Error: No provider could be determined from setup_provider.")
            return
        model = None
        key = keypart
    if not provider:
        print("Error: No provider could be determined from setup_provider.")
        return
    if model:
        mgr.set_provider_model_config(provider, model, key, value)
        print(f"Set config for provider '{provider}', model '{model}': {key} = {value}")
    else:
        mgr.set_provider_config(provider, key, value)
        print(f"Set config for provider '{provider}': {key} = {value}")

def handle_list_providers():
    list_providers()

def handle_list_models(args):
    """
    List models for the specified or current provider, using provider.get_model_info().
    """
    provider_instance = get_provider_instance()
    provider_name = getattr(provider_instance, 'name', None)
    if not provider_name:
        print("Error: Provider must be specified with --provider or set as default before listing models.")
        sys.exit(1)
    try:
        models = list(provider_instance.get_model_info().values())
        if models and isinstance(models[0], dict):
            _print_models_table(models, provider_name)
        else:
            print(f"Supported models for provider '{provider_name}':")
            for m in models:
                print(f"- {m}")
    except Exception as e:
        print(f"Error listing models for provider '{provider_name}': {e}")
    sys.exit(0)

def _print_models_table(models, provider_name):
    from rich.table import Table
    from rich.console import Console
    headers = ["name", "open", "context", "max_input", "max_cot", "max_response", "thinking_supported", "driver"]
    display_headers = ["Model Name", "Vendor", "context", "max_input", "max_cot", "max_response", "Thinking", "Driver"]
    table = Table(title=f"Supported models for provider '{provider_name}'")
    _add_table_columns(table, display_headers)
    num_fields = {"context", "max_input", "max_cot", "max_response"}
    for m in models:
        row = [str(m.get("name", ""))]
        row.extend(_build_model_row(m, headers, num_fields))
        table.add_row(*row)
    console = Console()
    console.print(table)

def _add_table_columns(table, display_headers):
    for i, h in enumerate(display_headers):
        justify = "right" if i == 0 else "center"
        table.add_column(h, style="bold", justify=justify)

def _format_k(val):
    try:
        n = int(val)
        if n >= 1000:
            return f"{n // 1000}k"
        return str(n)
    except Exception:
        return str(val)

def _build_model_row(m, headers, num_fields):
    # Extend for driver column
    def format_driver(val):
        if isinstance(val, (list, tuple)):
            return ', '.join(val)
        val_str = str(val)
        # Remove only a trailing 'ModelDriver', but keep names like 'OpenAIResponses'
        return val_str.removesuffix('ModelDriver').strip()

    row = []
    for h in headers[1:]:
        v = m.get(h, "")
        if h in num_fields and v not in ("", "N/A"):
            if h in ("context", "max_input") and isinstance(v, (list, tuple)) and len(v) == 2:
                row.append(f"{_format_k(v[0])} / {_format_k(v[1])}")
            else:
                row.append(_format_k(v))
        elif h == "open":
            row.append("Open" if v is True or v == "Open" else "Locked")
        elif h == "thinking_supported":
            row.append("📖" if v is True or v == "True" else "")
        elif h == "driver":
            row.append(format_driver(v))
        else:
            row.append(str(v))
        # Add driver to last column if present in headers

    return row

def handle_model_selection(args):
    if getattr(args, 'model', None):
        provider_instance = get_provider_instance()
        provider_name = getattr(provider_instance, 'name', None)

        if not provider_name:
            print("Error: Provider must be specified with --provider or set as default before selecting a model.")
            sys.exit(1)
        if not validate_model_for_provider(provider_name, args.model):
            sys.exit(1)
        config.runtime_set('model', args.model)

def set_default_system_prompt(args):
    if not getattr(args, 'system', None):
        args.system = "You are an LLM agent. Respond to the user prompt as best as you can."

def validate_model_for_provider(provider_name, model_name):
    """
    Check if the given model is available for the provider.
    Returns True if available, False otherwise.
    """
    try:
        provider_instance = get_provider_instance()
        info_dict = provider_instance.get_model_info()
        available_names = [m["name"] for m in info_dict.values() if isinstance(m, dict) and "name" in m]
        if model_name in available_names:
            return True
        else:
            print(f"Error: Model '{model_name}' is not available for provider '{provider_name}'.")
            print(f"Available models: {', '.join(available_names)}")
            return False
    except Exception as e:
        print(f"Error validating model for provider '{provider_name}': {e}")
        return False

def dispatch_command(args, mgr, parser):
    if args.list_tools:
        handle_list_tools()
    elif args.set_api_key:
        handle_set_api_key(args, mgr)
    elif args.set_provider:
        handle_set_provider(args, mgr)
    elif args.set:
        handle_set_provider_kv(args, mgr)
    elif args.list_providers:
        handle_list_providers()
    elif args.user_prompt:
        from janito.cli.single_shot_mode.handler import PromptHandler as SingleShotPromptHandler
        handler = SingleShotPromptHandler(args)
        handler.handle()
        # Mimic the original logic, though handle() returns None, so treat as successful
        ret = True  # you may adapt this if handle() can indicate failure
        if not ret:
            parser.print_help()
    else:
        handle_chat_mode(args, parser)

def handle_chat_mode(args, parser):
    # If no user prompt is provided, start the chat mode
    termweb_proc = None
    try:
        if not getattr(args, 'no_termweb', False):
            from janito.cli.termweb_starter import start_termweb
            from janito.cli.config import set_termweb_port, get_termweb_port
            set_termweb_port(getattr(args, 'termweb_port', get_termweb_port()))
            try:
                provider_instance = get_provider_instance()
            except RuntimeError as e:
                from rich.console import Console
                Console().print(f'[red][bold]Error:[/bold] {e}[/red]')
                return
            termweb_proc, started, termweb_stdout_path, termweb_stderr_path = start_termweb(get_termweb_port())
        from janito.cli.chat_mode.chat_entry import main as chat_mode_main
        chat_mode_main()
    finally:
        if termweb_proc:
            termweb_proc.terminate()
            termweb_proc.wait()

def main():
    """
    Entry point for the janito CLI.
    Parses command-line arguments and executes the corresponding actions.
    """
    # Bootstrap runtime config with defaults
    from janito.cli.config_defaults import bootstrap_runtime_config_from_defaults
    bootstrap_runtime_config_from_defaults()

    parser = argparse.ArgumentParser(description="Janito CLI")
    parser.add_argument('--version', action='version', version=f'%(prog)s {VERSION}')
    parser.add_argument('--list-tools', action='store_true', help='List all registered tools')
    parser.add_argument('--list-providers', action='store_true', help='List all supported LLM providers')
    parser.add_argument('-l', '--list-models', action='store_true', help='List all supported models for the current or selected provider')
    parser.add_argument('--set-api-key', metavar='API_KEY', help='Set API key for the current or selected provider')
    parser.add_argument('--set-provider', metavar='PROVIDER', help='Set the current LLM provider (stores in ~/.janito/config.json)')
    parser.add_argument('--set', metavar='[PROVIDER_NAME.]KEY=VALUE', help="Set a config key for a provider (e.g. --set openai.base_url=https://api.openai.com or --set model=gpt-3)")
    parser.add_argument('-s', '--system', metavar='SYSTEM_PROMPT', help='Set a system prompt for the LLM agent')
    parser.add_argument('-r', '--role', metavar='ROLE', help='Set the role for the agent (overrides config)')
    parser.add_argument('-p', '--provider', metavar='PROVIDER', help='Select the LLM provider (overrides config)')
    parser.add_argument('-m', '--model', metavar='MODEL', help='Select the model for the provider (overrides config)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Print extra information before answering')
    parser.add_argument('-R', '--raw', action='store_true', help='Print the raw JSON response from the OpenAI API (if applicable)')
    parser.add_argument('-e', '--event-log', action='store_true', help='Log events to the console as they are published')
    parser.add_argument('-t', '--temperature', type=float, default=None, help='Temperature for the language model (default: provider default)')
    parser.add_argument('--no-termweb', action='store_true', help='Disable the builtin lightweight web file viewer for terminal links (enabled by default)')
    parser.add_argument('--termweb-port', type=int, default=8088, help='Port for the termweb server (default: 8088)')
    parser.add_argument('user_prompt', nargs=argparse.REMAINDER, help='Prompt to submit (if no other command is used)')

    args = parser.parse_args()

    # Apply CLI args as runtime config overrides
    cli_overrides = {key: getattr(args, key) for key in ['provider', 'model', 'role', 'temperature', 'system'] if getattr(args, key, None) is not None}
    if 'system' in cli_overrides:
        cli_overrides['system_prompt'] = cli_overrides.pop('system')
    config.apply_runtime_overrides(cli_overrides)

    set_default_system_prompt(args)

    if getattr(args, 'list_models', False):
        handle_list_models(args)

    handle_model_selection(args)

    # Validate model for provider using the canonical config (with runtime overrides)
    provider = config.get('provider')
    model = config.get('model')
    if provider and model:
        if not validate_model_for_provider(provider, model):
            print(f"[red]Error: Model '{model}' is not available for provider '{provider}'.[/red]")
            sys.exit(1)

    from janito.cli.rich_terminal_reporter import RichTerminalReporter
    _rich_ui_manager = RichTerminalReporter(raw_mode=args.raw)

    dispatch_command(args, config, parser)

if __name__ == "__main__":
    main()
