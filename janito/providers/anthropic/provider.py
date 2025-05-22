from janito.llm.provider import LLMProvider
from janito.llm.model import LLMModelInfo
from janito.llm.auth import LLMAuthManager
from janito.llm.driver_config import LLMDriverConfig
from janito.tool_registry import ToolRegistry
from janito.providers.registry import LLMProviderRegistry

from .model_info import MODEL_SPECS

class AnthropicProvider(LLMProvider):
    name = "anthropic"
    MODEL_SPECS = MODEL_SPECS
    DEFAULT_MODEL = "claude-3-opus-20240229"

    def __init__(self, auth_manager: LLMAuthManager = None, config: LLMDriverConfig = None):
        self.auth_manager = auth_manager or LLMAuthManager()
        self._api_key = self.auth_manager.get_credentials(type(self).name)
        self._tool_registry = ToolRegistry()
        self._info = config or LLMDriverConfig(model=None)
        if not self._info.model:
            self._info.model = self.DEFAULT_MODEL
        if not self._info.api_key:
            self._info.api_key = self._api_key
        self.fill_missing_device_info(self._info)
        from janito.drivers.anthropic.driver import AnthropicModelDriver
        self._driver = AnthropicModelDriver(self._info, self._tool_registry)

    @property
    def driver(self):
        return self._driver

LLMProviderRegistry.register(AnthropicProvider.name, AnthropicProvider)
