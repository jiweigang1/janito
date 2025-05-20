from janito.llm_provider import LLMProvider
from janito.llm_model_info import ModelInfo
from janito.llm_auth_manager import LLMAuthManager
from janito.drivers.google_genai.driver import GoogleGenaiModelDriver
from janito.tool_registry import ToolRegistry
from janito.providers.registry import LLMProviderRegistry

from .model_info import MODEL_SPECS

class GoogleProvider(LLMProvider):
    MODEL_SPECS = MODEL_SPECS
    """
    Provider for Google LLMs via google-google.
    Default model: 'gemini-2.5-pro-preview-05-06'.
    """
    name = "google"

    DEFAULT_MODEL = "gemini-2.5-pro-preview-05-06"

    def __init__(self, config: dict = None):
        self._auth_manager = LLMAuthManager()
        self._api_key = self._auth_manager.get_credentials(type(self).name)
        self._tool_registry = ToolRegistry()
        self._config = config or {}
        if 'model_name' not in self._config:
            self._config['model_name'] = self.DEFAULT_MODEL
        self._driver = GoogleGenaiModelDriver(
            type(self).name,
            self._api_key,
            self._config,
            self._tool_registry
        )

    @property
    def driver(self) -> GoogleGenaiModelDriver:
        return self._driver

    def execute_tool(self, tool_name: str, event_bus, *args, **kwargs):
        from janito.tool_executor import ToolExecutor
        executor = ToolExecutor(registry=self._tool_registry, event_bus=event_bus)
        return executor.execute_by_name(tool_name, *args, **kwargs)

LLMProviderRegistry.register(GoogleProvider.name, GoogleProvider)
