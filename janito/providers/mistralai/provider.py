from janito.llm_provider import LLMProvider
from janito.llm_model_info import ModelInfo
from janito.llm_auth_manager import LLMAuthManager
from janito.drivers.mistralai.driver import MistralAIModelDriver
from janito.tool_registry import ToolRegistry
from janito.providers.registry import LLMProviderRegistry

from .model_info import MODEL_SPECS

class MistralAIProvider(LLMProvider):
    provider_name = "mistralai"

    DEFAULT_MODEL = "mistral-medium-latest"

    def __init__(self, auth_manager: LLMAuthManager = None, model_name: str = None):
        self.auth_manager = auth_manager or LLMAuthManager()
        self._api_key = self.auth_manager.get_credentials(type(self).provider_name)
        self._tool_registry = ToolRegistry()
        self._model_name = model_name if model_name else self.DEFAULT_MODEL
        self._driver = MistralAIModelDriver(type(self).provider_name, self._model_name, self._api_key, self._tool_registry)

    def get_model_name(self) -> str:
        return self._model_name

    @property
    def driver(self):
        return self._driver

    def execute_tool(self, tool_name: str, event_bus, *args, **kwargs):
        from janito.tool_executor import ToolExecutor
        executor = ToolExecutor(registry=self._tool_registry, event_bus=event_bus)
        return executor.execute_by_name(tool_name, *args, **kwargs)

LLMProviderRegistry.register(MistralAIProvider.provider_name, MistralAIProvider)
