"""
ProviderConfigManager: Handles reading and writing provider configuration for janito.
"""
from janito.config_manager import ConfigManager
from janito.cli.config_defaults import CONFIG_DEFAULTS
from janito.llm.auth import LLMAuthManager

# Singleton for provider config usage
config = ConfigManager(config_path=None, defaults=CONFIG_DEFAULTS)

def get_default_provider():
    return config.get('provider')

def set_default_provider(provider_name):
    config.file_set('provider', provider_name)

def get_config_path():
    return str(config.config_path)

def set_api_key(provider, api_key):
    auth_manager = LLMAuthManager()
    auth_manager.set_credentials(provider, api_key)

def get_provider_config(provider):
    return config.get_provider_config(provider)

def set_provider_config(provider, key, value):
    # Update provider config and persist immediately
    cfg = config.file_config.get('providers', {})
    if provider not in cfg:
        cfg[provider] = {}
    cfg[provider][key] = value
    config.file_config['providers'] = cfg
    with open(config.config_path, "w", encoding="utf-8") as f:
        json.dump(config.file_config, f, indent=2)

def set_provider_model_config(provider, model, key, value):
    # Update provider-model config and persist immediately
    cfg = config.file_config.get('providers', {})
    if provider not in cfg:
        cfg[provider] = {}
    if 'models' not in cfg[provider]:
        cfg[provider]['models'] = {}
    if model not in cfg[provider]['models']:
        cfg[provider]['models'][model] = {}
    cfg[provider]['models'][model][key] = value
    config.file_config['providers'] = cfg
    with open(config.config_path, "w", encoding="utf-8") as f:
        json.dump(config.file_config, f, indent=2)

def get_provider_model_config(provider, model):
    return config.get_provider_model_config(provider, model)

