"""Handlers for set-type CLI commands (provider, model, api keys, etc)."""

from janito.provider_config import set_default_provider
from janito.config import config as global_config
from janito.provider_registry import ProviderRegistry
from janito.cli.cli_commands.set_api_key import handle_set_api_key

def handle_api_key_set(args, config_mgr=None):
    if getattr(args, "set_api_key", None):
        handle_set_api_key(args, config_mgr) if config_mgr else None
        return True
    return False

def handle_set(args, config_mgr=None):
    set_arg = getattr(args, 'set', None)
    if not set_arg:
        return False
    try:
        if '=' not in set_arg:
            print("Error: --set requires KEY=VALUE (e.g., --set default_provider=provider_name).")
            return True
        key, value = set_arg.split('=', 1)
        key, value = key.strip(), value.strip()
        if key == 'default_provider':
            return _handle_set_default_provider(value)
        elif '.default_model' in key:
            return _handle_set_default_model(key, value)
        else:
            print(f"Error: Unknown config key '{key}'. Supported: default_provider, <provider>.default_model")
            return True
    except Exception as e:
        print(f"Error parsing --set value: {e}")
        return True

def _handle_set_default_provider(value):
    try:
        supported = ProviderRegistry().get_provider(value)
    except Exception:
        print(f"Error: Provider '{value}' is not supported. Run '--list-providers' to see the supported list.")
        return True
    set_default_provider(value)
    print(f"Default provider set to '{value}'.")
    return True

def _handle_set_default_model(key, value):
    provider_name, suffix = key.split('.', 1)
    if suffix != "default_model":
        print(f"Error: Only <provider>.default_model is supported for provider-specific model override. Not: '{key}'")
        return True
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
    global_config.set_provider_config(provider_name, "default_model", value)
    print(f"Default model for provider '{provider_name}' set to '{value}'.")
    return True
