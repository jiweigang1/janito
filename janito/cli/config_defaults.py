# Centralized config defaults for Janito CLI
CONFIG_DEFAULTS = {
    "api_key": None,  # Must be set by user
    "model": "gpt-4.1",  # Default model
    "role": "software developer",  # Part of the Agent Profile

    "temperature": 0.2,
    "max_tokens": 32000,
    "use_azure_openai": False,
    "azure_openai_api_version": "2023-05-15",
    "profile": "base",
}

def bootstrap_runtime_config_from_defaults(runtime_config):
    """
    Ensure that all keys from CONFIG_DEFAULTS are set in runtime_config
    unless they already exist. This provides predictable defaults for all
    runtime config accesses, especially useful at CLI or agent startup.
    """
    for k, v in CONFIG_DEFAULTS.items():
        if k not in runtime_config.all():
            runtime_config.set(k, v)
