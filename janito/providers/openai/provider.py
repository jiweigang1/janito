from janito.llm_provider import LLMProvider
from janito.llm_auth_manager import LLMAuthManager
from janito.drivers.openai.driver import OpenAIModelDriver
from janito.tool_executor import ToolExecutor
from janito.tool_registry import ToolRegistry
from janito.providers.registry import LLMProviderRegistry

class OpenAIProvider(LLMProvider):
    DEFAULT_MODEL = "gpt-4.1"

    def __init__(self, auth_manager: LLMAuthManager = None):
        self.auth_manager = auth_manager or LLMAuthManager()
        self._api_key = self.auth_manager.get_credentials("openai")
        self._tool_registry = ToolRegistry()
        self._driver = OpenAIModelDriver("openai", self.DEFAULT_MODEL, self._api_key, self._tool_registry)

    def get_model_name(self) -> str:
        return self.DEFAULT_MODEL

    @property
    def driver(self) -> OpenAIModelDriver:
        return self._driver

    def execute_tool(self, tool_name: str, event_bus, *args, **kwargs):
        executor = ToolExecutor(registry=self._tool_registry, event_bus=event_bus)
        return executor.execute_by_name(tool_name, *args, **kwargs)

LLMProviderRegistry.register("openai", OpenAIProvider)
