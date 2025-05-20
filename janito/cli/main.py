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

from janito.cli.cli_commands.dispatch import dispatch_command
from janito.cli.cli_commands.list_models import handle_list_models
from janito.cli.cli_commands.model_selection import handle_model_selection, validate_model_for_provider
from janito.cli.cli_commands.system_prompt import set_default_system_prompt

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

def main():
    """
    Entry point for the janito CLI.
    Parses command-line arguments and executes the corresponding actions.
    """
    # Bootstrap runtime config with defaults
    parser = argparse.ArgumentParser(description="Janito CLI")
    parser.add_argument('--version', action='version', version=f'%(prog)s {VERSION}')
    parser.add_argument('--list-tools', action='store_true', help='List all registered tools')
    parser.add_argument('--show-config', action='store_true', help='Show the current configuration')
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
