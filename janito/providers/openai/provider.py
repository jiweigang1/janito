from janito.llm_provider import LLMProvider
from janito.llm_model_info import ModelInfo
from janito.llm_auth_manager import LLMAuthManager
from janito.drivers.openai.driver import OpenAIModelDriver
from janito.drivers.openai_responses.driver import OpenAIResponsesModelDriver
from janito.tool_executor import ToolExecutor
from janito.tool_registry import ToolRegistry
from janito.providers.registry import LLMProviderRegistry

from .model_info import MODEL_SPECS

class OpenAIProvider(LLMProvider):
    name = "openai"


    MODEL_SPECS = MODEL_SPECS
    DEFAULT_MODEL = "gpt-4.1"  # Options: gpt-4.1, gpt-4o, o3-mini, o4-mini, o4-mini-high

    def __init__(self, auth_manager: LLMAuthManager = None, config: dict = None):
        self.auth_manager = auth_manager or LLMAuthManager()
        self._api_key = self.auth_manager.get_credentials(type(self).name)
        self._tool_registry = ToolRegistry()
        self._config = config or {}
        self._model_name = self._config.get('model_name', self.DEFAULT_MODEL)

        self._driver = self.get_driver_for_model(config=self._config)


    @property
    def driver(self) -> OpenAIResponsesModelDriver:
        return self._driver

    def execute_tool(self, tool_name: str, event_bus, *args, **kwargs):
        executor = ToolExecutor(registry=self._tool_registry, event_bus=event_bus)
        return executor.execute_by_name(tool_name, *args, **kwargs)


LLMProviderRegistry.register(OpenAIProvider.name, OpenAIProvider)
