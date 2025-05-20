from janito.config_manager import ConfigManager
# Centralized config defaults for Janito CLI
CONFIG_DEFAULTS = {
    "api_key": None,  # Must be set by user
    "provider": "openai",  # Default provider (OpenAI, can be overridden by user with --provider)
    "model": "gpt-4.1",  # Default model (available: gpt-4.1, gpt-4o, gpt-4-turbo, o3-mini, o4-mini, o4-mini-high)
    "role": "software developer",  # Part of the Agent Profile
    "temperature": 0.2,
    "max_tokens": 32000,
    "use_azure_openai": False,
    "azure_openai_api_version": "2023-05-15",
    "profile": "base",
}

# Singleton for CLI usage
config = ConfigManager(config_path=None, defaults=CONFIG_DEFAULTS)

CONFIG_OPTIONS = {
    "api_key": "API key for OpenAI-compatible service (required)",  # pragma: allowlist secret
    "trust": "Trust mode: suppress all console output (bool, default: False)",
    "model": "Model name to use (e.g., 'gpt-4.1', 'gpt-4o', 'gpt-4-turbo', 'o3-mini', 'o4-mini', 'o4-mini-high')",
    "base_url": "API base URL (OpenAI-compatible endpoint)",
    "role": "Role description for the Agent Profile (e.g., 'software engineer')",
    "temperature": "Sampling temperature (float, e.g., 0.0 - 2.0)",
    "max_tokens": "Maximum tokens for model response (int)",
    "use_azure_openai": "Whether to use Azure OpenAI client (default: False)",
    "template": "Template context dictionary for Agent Profile prompt rendering (nested)",
    "profile": "Agent Profile name (only 'base' is supported)",
}

DEFAULT_TERMWEB_PORT = 8088

def get_termweb_port():
    port = config.get("termweb_port")
    try:
        return int(port)
    except Exception:
        return DEFAULT_TERMWEB_PORT

def set_termweb_port(port):
    config.file_set("termweb_port", int(port))
