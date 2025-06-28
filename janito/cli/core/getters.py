"""Handlers for get-type CLI commands (show_config, list_providers, models, tools)."""
import sys

from janito.cli.cli_commands.list_providers import handle_list_providers
from janito.cli.cli_commands.list_models import handle_list_models
from janito.cli.cli_commands.list_tools import handle_list_tools
from janito.cli.cli_commands.show_config import handle_show_config
from functools import partial
from janito.provider_registry import ProviderRegistry

GETTER_KEYS = ["show_config", "list_providers", "list_models", "list_tools"]


def handle_getter(args, config_mgr=None):
    provider_instance = None
    if getattr(args, "list_models", False):
        provider = getattr(args, "provider", None)
        if not provider:
            import sys
            print(
                "Error: No provider selected. Please set a provider using '-p PROVIDER', '--set provider=name', or configure a provider."
            )
            sys.exit(1)
        provider_instance = ProviderRegistry().get_instance(provider)
    GETTER_DISPATCH = {
        "list_providers": partial(handle_list_providers, args),
        "list_models": partial(handle_list_models, args, provider_instance),
        "list_tools": partial(handle_list_tools, args),
        "show_config": partial(handle_show_config, args),
    }
    for arg in GETTER_KEYS:
        if getattr(args, arg, False) and arg in GETTER_DISPATCH:
            return GETTER_DISPATCH[arg]()
