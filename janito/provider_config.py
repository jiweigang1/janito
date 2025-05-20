"""
ProviderConfigManager: Handles reading and writing provider configuration for janito.
"""
from janito.config_manager import ConfigManager
from janito.cli.config_defaults import CONFIG_DEFAULTS
from janito.llm_auth_manager import LLMAuthManager

# Singleton for provider config usage
config = ConfigManager(config_path=None, defaults=CONFIG_DEFAULTS)

def get_default_provider():
    return config.get('provider')

def set_default_provider(provider_name):
    config.set('provider', provider_name)
    config.save()

def get_config_path():
    return str(config.config_path)

def set_api_key(provider, api_key):
    auth_manager = LLMAuthManager()
    auth_manager.set_credentials(provider, api_key)

def get_provider_config(provider):
    return config.get_provider_config(provider)

def set_provider_config(provider, key, value):
    config.set_provider_config(provider, key, value)
    config.save()

def set_provider_model_config(provider, model, key, value):
    config.set_provider_model_config(provider, model, key, value)
    config.save()

def get_provider_model_config(provider, model):
    return config.get_provider_model_config(provider, model)

def list_configured_providers():
    return config.list_configured_providers()
