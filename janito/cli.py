"""
janito.cli: Command Line Interface for janito

Provides commands for managing API keys and interacting with LLM providers.
"""
import argparse
import sys
from janito.version import __version__ as VERSION
from janito.provider_registry import list_providers, select_provider
from janito.prompt_handler import handle_prompt
from janito.provider_config import ProviderConfigManager
from rich.console import Console
from rich.pretty import Pretty

def log_event_to_console(event):
    console = Console()
    console.print(f"[EVENT] [bold cyan]{event.__class__.__name__}[/]:", Pretty(event.__dict__, expand_all=True))

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
        event_bus.subscribe(Event, log_event_to_console)
    result = handle_prompt(args)
    if args.raw and result is not None:
        print(result)
    return True

def main():
    """
    Entry point for the janito CLI.
    Parses command-line arguments and executes the corresponding actions.
    """
    parser = argparse.ArgumentParser(description="Janito CLI")
    parser.add_argument('--version', action='version', version=f'%(prog)s {VERSION}')
    parser.add_argument('--list-tools', action='store_true', help='List all registered tools')
    parser.add_argument('--list-providers', action='store_true', help='List all supported LLM providers')
    parser.add_argument('--set-api-key', nargs=2, metavar=('PROVIDER', 'API_KEY'), help='Set API key for a provider')
    parser.add_argument('--set-provider', metavar='PROVIDER', help='Set the current LLM provider (stores in ~/janito/config.json)')
    parser.add_argument('--set-config', nargs=3, metavar=('PROVIDER', 'KEY', 'VALUE'), help='Set a provider-specific config value (e.g., thinking_budget)')
    parser.add_argument('-s', '--system', metavar='SYSTEM_PROMPT', help='Set a system prompt for the LLM agent')
    parser.add_argument('-p', '--provider', metavar='PROVIDER', help='Select the LLM provider (overrides config)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Print extra information before answering')
    parser.add_argument('-r', '--raw', action='store_true', help='Print the raw JSON response from the OpenAI API (if applicable)')
    parser.add_argument('--tb', '--thinking_budget', dest='thinking_budget', type=int, default=None, help='Set thinking_budget for this prompt (Gemini only)')
    parser.add_argument('-e', '--event-log', action='store_true', help='Log events to the console as they are published')
    parser.add_argument('user_prompt', nargs=argparse.REMAINDER, help='Prompt to submit (if no other command is used)')

    args = parser.parse_args()

    # Dispatch table for argument handlers
    mgr = ProviderConfigManager()
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
        parser.print_help()

if __name__ == "__main__":
    main()
