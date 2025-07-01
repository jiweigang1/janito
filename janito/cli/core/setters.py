"""Handlers for set-type CLI commands (provider, model, api keys, etc)."""

from janito.provider_config import set_config_provider
from janito.config import config as global_config
from janito.provider_registry import ProviderRegistry
from janito.cli.cli_commands.set_api_key import handle_set_api_key


def handle_api_key_set(args):
    if getattr(args, "set_api_key", None):
        handle_set_api_key(args)
        return True
    return False


def handle_set(args, config_mgr=None):
    set_arg = getattr(args, "set", None)
    if not set_arg:
        return False
    try:
        if not _validate_set_arg_format(set_arg):
            return True
        key, value = _parse_set_arg(set_arg)
        key = key.replace("-", "_")
        return _dispatch_set_key(key, value)
    except Exception as e:
        print(f"Error parsing --set value: {e}")
        return True

def _validate_set_arg_format(set_arg):
    if "=" not in set_arg:
        print(
            "Error: --set requires KEY=VALUE (e.g., --set provider=provider_name)."
        )
        return False
    return True

def _parse_set_arg(set_arg):
    key, value = set_arg.split("=", 1)
    return key.strip(), value.strip()

def _dispatch_set_key(key, value):
    if key == "provider":
        return _handle_set_config_provider(value)
    if key == "model":
        return _handle_set_global_model(value)
    if "." in key and key.endswith(".model"):
        return _handle_set_provider_model(key, value)
    if key == "max_tokens":
        return _handle_set_max_tokens(value)
    if key == "base_url":
        return _handle_set_base_url(value)
    if key in ["azure_deployment_name", "azure-deployment-name"]:
        global_config.file_set("azure_deployment_name", value)
        print(f"Azure deployment name set to '{value}'.")
        return True
    if ".max_tokens" in key or ".base_url" in key:
        return _handle_set_provider_level_setting(key, value)
    if key == "tool_permissions":
        from janito.tools.permissions_parse import parse_permissions_string
        from janito.tools.permissions import set_global_allowed_permissions
        perms = parse_permissions_string(value)
        global_config.file_set("tool_permissions", value)
        set_global_allowed_permissions(perms)
        print(f"Tool permissions set to '{value}' (parsed: {perms})")
        return True
    print(
        f"Error: Unknown config key '{key}'. Supported: provider, model, <provider>.model, max_tokens, base_url, azure_deployment_name, <provider>.max_tokens, <provider>.base_url, <provider>.<model>.max_tokens, <provider>.<model>.base_url, tool_permissions"
    )
    return True


def _handle_set_max_tokens(value):
    try:
        ival = int(value)
    except Exception:
        print("Error: max_tokens must be set to an integer value.")
        return True
    global_config.file_set("max_tokens", ival)
    print(f"Top-level max_tokens set to {ival}.")
    return True


def _handle_set_base_url(value):
    global_config.file_set("base_url", value)
    print(f"Top-level base_url set to {value}.")
    return True


def _handle_set_provider_level_setting(key, value):
    parts = key.split(".")
    if len(parts) == 2:
        provider, par_key = parts
        if par_key == "max_tokens":
            try:
                ival = int(value)
            except Exception:
                print("Error: max_tokens must be set to an integer value.")
                return True
            global_config.set_provider_config(provider, "max_tokens", ival)
            print(f"max_tokens for provider '{provider}' set to {ival}.")
            return True
        if par_key == "base_url":
            global_config.set_provider_config(provider, "base_url", value)
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
            global_config.set_provider_model_config(provider, model, "max_tokens", ival)
            print(
                f"max_tokens for provider '{provider}', model '{model}' set to {ival}."
            )
            return True
        if mk == "base_url":
            global_config.set_provider_model_config(provider, model, "base_url", value)
            print(
                f"base_url for provider '{provider}', model '{model}' set to {value}."
            )
            return True
    print(
        f"Error: Unknown config key '{key}'. Supported: provider, model, <provider>.model, max_tokens, base_url, <provider>.max_tokens, <provider>.base_url, <provider>.<model>.max_tokens, <provider>.<model>.base_url"
    )
    return True


def _handle_set_config_provider(value):
    try:
        supported = ProviderRegistry().get_provider(value)
    except Exception:
        print(
            f"Error: Provider '{value}' is not supported. Run '--list-providers' to see the supported list."
        )
        return True
    from janito.provider_config import set_config_provider

    set_config_provider(value)
    print(f"Provider set to '{value}'.")
    return True


def _handle_set_provider_model(key, value):
    provider_name, suffix = key.rsplit(".", 1)
    if suffix != "model":
        print(
            f"Error: Only <provider>.model is supported for provider-specific model override. Not: '{key}'"
        )
        return True
    try:
        provider_cls = ProviderRegistry().get_provider(provider_name)
        provider_instance = provider_cls()
    except Exception:
        print(
            f"Error: Provider '{provider_name}' is not supported. Run '--list-providers' to see the supported list."
        )
        return True
    model_info = provider_instance.get_model_info(value)
    if not model_info:
        print(
            f"Error: Model '{value}' is not defined for provider '{provider_name}'. Run '-p {provider_name} -l' to see models."
        )
        return True
    global_config.set_provider_config(provider_name, "model", value)
    print(f"Default model for provider '{provider_name}' set to '{value}'.")
    return True


def _handle_set_global_model(value):
    # Try to validate model choice (against current provider if possible)
    provider_name = global_config.get("provider")
    if provider_name:
        try:
            provider_cls = ProviderRegistry().get_provider(provider_name)
            provider_instance = provider_cls()
            model_info = provider_instance.get_model_info(value)
            if not model_info:
                print(
                    f"Error: Model '{value}' is not defined for provider '{provider_name}'. Run '-p {provider_name} -l' to see models."
                )
                return True
        except Exception:
            print(
                f"Warning: Could not validate model for provider '{provider_name}'. Setting anyway."
            )
    else:
        print(
            "Warning: No provider set. Model will be set globally, but may not be valid for any provider."
        )
    global_config.file_set("model", value)
    print(f"Global default model set to '{value}'.")
    return True
