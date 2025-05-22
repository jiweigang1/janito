"""
ProviderConfigManager: Handles reading and writing provider configuration for janito.
"""
from janito.config import config
from janito.llm.auth import LLMAuthManager

def get_default_provider():
    return config.get('default_provider')

def set_default_provider(provider_name):
    config.file_set('default_provider', provider_name)

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

def get_effective_setting(provider, model, setting):
    """
    Look up setting with the following order:
      1. providers.{provider}.models.{model}.{setting}
      2. providers.{provider}.{setting}
      3. top-level {setting}
      Returns None if not found.
    """
    # 1. provider-model
    val = config.get_provider_model_config(provider, model).get(setting)
    if val is not None:
        return val
    # 2. provider
    val = config.get_provider_config(provider).get(setting)
    if val is not None:
        return val
    # 3. top-level
    val = config.get(setting)
    return val
