"""
ProviderConfigManager: Handles reading and writing provider configuration for janito.
"""
import os
import json
from typing import Optional, Any
from janito.llm_auth_manager import LLMAuthManager

class ProviderConfigManager:
    """
    Manages the provider configuration file for janito.
    By default, config is stored at ~/janito/config.json.
    Supports provider-specific configuration.
    """
    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            config_path = os.path.expanduser('~/janito/config.json')
        self.config_path = config_path
        self.config_dir = os.path.dirname(self.config_path)

    def _load_config(self) -> dict:
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_config(self, config: dict) -> None:
        os.makedirs(self.config_dir, exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)

    def get_default_provider(self) -> Optional[str]:
        """Return the default provider from config, or None if unset."""
        config = self._load_config()
        return config.get('provider')

    def set_default_provider(self, provider_name: str) -> None:
        """Set the default provider in the config file."""
        config = self._load_config()
        config['provider'] = provider_name
        self._save_config(config)

    def get_config_path(self) -> str:
        """Return the config file path."""
        return self.config_path

    def set_api_key(self, provider: str, api_key: str):
        """Set API key for a provider."""
        auth_manager = LLMAuthManager()
        auth_manager.set_credentials(provider, api_key)

    def get_provider_config(self, provider: str) -> dict:
        """Get config dict for a specific provider. Returns empty dict if not set."""
        config = self._load_config()
        providers = config.get('providers', {})
        return providers.get(provider, {})

    def set_provider_config(self, provider: str, key: str, value: Any) -> None:
        """Set a config value for a specific provider."""
        config = self._load_config()
        if 'providers' not in config:
            config['providers'] = {}
        if provider not in config['providers']:
            config['providers'][provider] = {}
        config['providers'][provider][key] = value
        self._save_config(config)
