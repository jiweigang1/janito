from janito.llm_provider import LLMProvider
from janito.llm_auth_manager import LLMAuthManager
from janito.drivers.openai.driver import OpenAIModelDriver
from janito.tool_executor import ToolExecutor
from janito.tool_registry import ToolRegistry
from janito.providers.registry import LLMProviderRegistry

class OpenAIProvider(LLMProvider):
    DEFAULT_MODEL = "gpt-4.1"

    @classmethod
    def list_models(cls):
        """
        Return a list of supported OpenAI models with detailed fields.
        """
        return [
            {
                "name": "gpt-4.1",
                "open": "openai",
                "context": "1 047 576",
                "max_input": "1 014 808",
                "max_cot": "N/A",
                "max_response": "32 768",
                "thinking_supported": "",
                "default_temp": 0.2
            },
            {
                "name": "gpt-4o",
                "open": "openai",
                "context": "128 000",
                "max_input": "123 904",
                "max_cot": "N/A",
                "max_response": "4 096",
                "thinking_supported": "",
                "default_temp": 0.2
            },
            {
                "name": "gpt-4-turbo",
                "open": "openai",
                "context": "128 000",
                "max_input": "123 904",
                "max_cot": "N/A",
                "max_response": "4 096",
                "thinking_supported": "",
                "default_temp": 0.2
            },
            {
                "name": "gpt-4",
                "open": "openai",
                "context": "8 192",
                "max_input": "4 096*",
                "max_cot": "N/A",
                "max_response": "4 096",
                "thinking_supported": "",
                "default_temp": 0.2
            },
            {
                "name": "o3-mini",
                "open": "openai",
                "context": "200 000",
                "max_input": "100 000",
                "max_cot": "N/A",
                "max_response": "100 000",
                "thinking_supported": "Yes",
                "default_temp": 0.2
            },
            {
                "name": "o4-mini",
                "open": "openai",
                "context": "200 000",
                "max_input": "100 000",
                "max_cot": "N/A",
                "max_response": "100 000",
                "thinking_supported": "Yes",
                "default_temp": 1
            },
            {
                "name": "o4-mini-high",
                "open": "openai",
                "context": "200 000",
                "max_input": "100 000",
                "max_cot": "N/A",
                "max_response": "100 000",
                "thinking_supported": "Yes",
                "default_temp": 0.2
            }
        ]

    def __init__(self, auth_manager: LLMAuthManager = None, model_name: str = None):
        self.auth_manager = auth_manager or LLMAuthManager()
        self._api_key = self.auth_manager.get_credentials("openai")
        self._tool_registry = ToolRegistry()
        self._model_name = model_name if model_name else self.DEFAULT_MODEL
        self._driver = OpenAIModelDriver("openai", self._model_name, self._api_key, self._tool_registry)

    def get_model_name(self) -> str:
        return self._model_name

    @property
    def driver(self) -> OpenAIModelDriver:
        return self._driver

    def execute_tool(self, tool_name: str, event_bus, *args, **kwargs):
        executor = ToolExecutor(registry=self._tool_registry, event_bus=event_bus)
        return executor.execute_by_name(tool_name, *args, **kwargs)

LLMProviderRegistry.register("openai", OpenAIProvider)
