from janito.cli.config import config, CONFIG_DEFAULTS

def bootstrap_runtime_config_from_defaults():
    """
    Ensure that all keys from CONFIG_DEFAULTS are set in config unless they already exist.
    """
    for k, v in CONFIG_DEFAULTS.items():
        if k not in config.all():
            config.runtime_set(k, v)
