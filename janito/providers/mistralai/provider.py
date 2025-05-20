from janito.llm_provider import LLMProvider
from janito.llm_model_info import ModelInfo
from janito.llm_auth_manager import LLMAuthManager
from janito.drivers.mistralai.driver import MistralAIModelDriver
from janito.tool_registry import ToolRegistry
from janito.providers.registry import LLMProviderRegistry

from .model_info import MODEL_SPECS

class MistralAIProvider(LLMProvider):
    MODEL_SPECS = MODEL_SPECS
    name = "mistralai"

    DEFAULT_MODEL = "mistral-medium-latest"

    def __init__(self, auth_manager: LLMAuthManager = None, config: dict = None):
        self.auth_manager = auth_manager or LLMAuthManager()
        self._api_key = self.auth_manager.get_credentials(type(self).name)
        self._tool_registry = ToolRegistry()
        self._config = config or {}
        if 'model_name' not in self._config:
            self._config['model_name'] = self.DEFAULT_MODEL
        self._driver = MistralAIModelDriver(type(self).name, self._api_key, self._config, self._tool_registry)

    @property
    def driver(self):
        return self._driver

    def execute_tool(self, tool_name: str, event_bus, *args, **kwargs):
        from janito.tool_executor import ToolExecutor
        executor = ToolExecutor(registry=self._tool_registry, event_bus=event_bus)
        return executor.execute_by_name(tool_name, *args, **kwargs)

LLMProviderRegistry.register(MistralAIProvider.name, MistralAIProvider)
