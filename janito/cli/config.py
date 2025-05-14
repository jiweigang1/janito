import json
from pathlib import Path
from threading import Lock
from janito.cli.config_defaults import CONFIG_DEFAULTS

class SingletonMeta(type):
    _instances = {}
    _lock: Lock = Lock()
    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]

class BaseConfig:
    def __init__(self):
        self._data = {}
    def get(self, key, default=None):
        return self._data.get(key, default)
    def set(self, key, value):
        self._data[key] = value
    def all(self):
        return self._data

class FileConfig(BaseConfig):
    def __init__(self, path):
        super().__init__()
        self.path = Path(path).expanduser()
        self.load()
    def load(self):
        if self.path.exists():
            with open(self.path, "r", encoding="utf-8") as f:
                self._data = json.load(f)
                self._data = {k: v for k, v in self._data.items() if v is not None}
        else:
            self._data = {}
    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2)

class EffectiveConfig:
    """Read-only merged view of local and global configs"""
    def __init__(self, local_cfg, global_cfg):
        self.local_cfg = local_cfg
        self.global_cfg = global_cfg
    def get(self, key, default=None):
        for cfg in (self.local_cfg, self.global_cfg):
            val = cfg.get(key)
            if val is not None:
                if val is None:
                    continue
                return val
        if default is None and key in CONFIG_DEFAULTS:
            return CONFIG_DEFAULTS[key]
        return default
    def all(self):
        merged = {}
        for cfg in (self.global_cfg, self.local_cfg):
            merged.update(cfg.all())
        return merged

CONFIG_OPTIONS = {
    "api_key": "API key for OpenAI-compatible service (required)",  # pragma: allowlist secret
    "trust": "Trust mode: suppress all console output (bool, default: False)",
    "model": "Model name to use (e.g., 'gpt-4.1')",
    "base_url": "API base URL (OpenAI-compatible endpoint)",
    "role": "Role description for the Agent Profile (e.g., 'software engineer')",
    "system_prompt_template": "Override the entire Agent Profile prompt text",
    "temperature": "Sampling temperature (float, e.g., 0.0 - 2.0)",
    "max_tokens": "Maximum tokens for model response (int)",
    "use_azure_openai": "Whether to use Azure OpenAI client (default: False)",
    # Accept template.* keys as valid config keys (for CLI validation, etc.)
    "template": "Template context dictionary for Agent Profile prompt rendering (nested)",
    "profile": "Agent Profile name (only 'base' is supported)",
    # Note: template.* keys are validated dynamically, not statically here
}

local_config = FileConfig(Path(".janito/config.json"))
global_config = FileConfig(Path.home() / ".janito/config.json")
effective_config = EffectiveConfig(local_config, global_config)
