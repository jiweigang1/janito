"""Handlers for set-type CLI commands (provider, model, api keys, etc)."""

from janito.provider_config import set_default_provider
from janito.config import config as global_config
from janito.provider_registry import ProviderRegistry
from janito.cli.cli_commands.set_api_key import handle_set_api_key

def handle_api_key_set(args):
    if getattr(args, "set_api_key", None):
        handle_set_api_key(args)
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
        key = key.replace('-', '_')

        if key == 'default_provider':
            return _handle_set_default_provider(value)
        if '.default_model' in key:
            return _handle_set_default_model(key, value)
        if key == 'max_tokens':
            return _handle_set_max_tokens(value)
        if key == 'base_url':
            return _handle_set_base_url(value)
        if '.max_tokens' in key or '.base_url' in key:
            return _handle_set_provider_level_setting(key, value)
        print(f"Error: Unknown config key '{key}'. Supported: default_provider, <provider>.default_model, max_tokens, base_url, <provider>.max_tokens, <provider>.base_url, <provider>.<model>.max_tokens, <provider>.<model>.base_url")
        return True
    except Exception as e:
        print(f"Error parsing --set value: {e}")
        return True


def _handle_set_max_tokens(value):
    try:
        ival = int(value)
    except Exception:
        print("Error: max_tokens must be set to an integer value.")
        return True
    global_config.file_set('max_tokens', ival)
    print(f"Top-level max_tokens set to {ival}.")
    return True


def _handle_set_base_url(value):
    global_config.file_set('base_url', value)
    print(f"Top-level base_url set to {value}.")
    return True


def _handle_set_provider_level_setting(key, value):
    parts = key.split('.')
    if len(parts) == 2:
        provider, par_key = parts
        if par_key == 'max_tokens':
            try:
                ival = int(value)
            except Exception:
                print("Error: max_tokens must be set to an integer value.")
                return True
            global_config.set_provider_config(provider, 'max_tokens', ival)
            print(f"max_tokens for provider '{provider}' set to {ival}.")
            return True
        if par_key == 'base_url':
            global_config.set_provider_config(provider, 'base_url', value)
            print(f"base_url for provider '{provider}' set to {value}.")
            return True
    elif len(parts) == 3:
        provider, model, mk = parts
        if mk == "max_tokens":
            try:
                ival = int(value)
            except Exception:
                print("Error: max_tokens must be set to an integer value.")
                return True
            global_config.set_provider_model_config(provider, model, 'max_tokens', ival)
            print(f"max_tokens for provider '{provider}', model '{model}' set to {ival}.")
            return True
        if mk == "base_url":
            global_config.set_provider_model_config(provider, model, 'base_url', value)
            print(f"base_url for provider '{provider}', model '{model}' set to {value}.")
            return True
    print(f"Error: Unknown config key '{key}'. Supported: default_provider, <provider>.default_model, max_tokens, base_url, <provider>.max_tokens, <provider>.base_url, <provider>.<model>.max_tokens, <provider>.<model>.base_url")
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
