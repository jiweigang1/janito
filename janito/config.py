# Shared Janito ConfigManager singleton
from janito.config_manager import ConfigManager

# Only one global instance! Used by CLI, provider_config, others:
config = ConfigManager(config_path=None)
