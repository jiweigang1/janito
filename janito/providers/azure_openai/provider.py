from janito.llm_provider import LLMProvider
from janito.llm_model_info import ModelInfo
from janito.llm_auth_manager import LLMAuthManager
from janito.tool_registry import ToolRegistry
from janito.providers.registry import LLMProviderRegistry

from .model_info import MODEL_SPECS

class AzureOpenAIProvider(LLMProvider):
    """
    Provider for Azure-hosted OpenAI LLMs.
    Default model: 'azure-gpt-35-turbo'.
    """
    MODEL_SPECS = MODEL_SPECS
    DEFAULT_MODEL = "azure-gpt-35-turbo"
    PROVIDER_NAME = "azure_openai"

    def __init__(self, model_name: str = None, config: dict = None):
        self._auth_manager = LLMAuthManager()
        self._api_key = self._auth_manager.get_credentials(self.PROVIDER_NAME)
        self._tool_registry = ToolRegistry()
        self._model_name = model_name if model_name else self.DEFAULT_MODEL
        self._params = config or {}
        self._driver = self.get_driver_for_model(self._model_name, config=self._config)

    def get_model_name(self) -> str:
        return self._model_name

    @property
    def driver(self):
        return self._driver

    def execute_tool(self, tool_name: str, event_bus, *args, **kwargs):
        from janito.tool_executor import ToolExecutor
        executor = ToolExecutor(registry=self._tool_registry, event_bus=event_bus)
        return executor.execute_by_name(tool_name, *args, **kwargs)

LLMProviderRegistry.register("azure_openai", AzureOpenAIProvider)
