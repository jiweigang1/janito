from janito.llm_provider import LLMProvider
from janito.llm_auth_manager import LLMAuthManager
from janito.drivers.mistralai.driver import MistralAIModelDriver
from janito.tool_registry import ToolRegistry
from janito.providers.registry import LLMProviderRegistry

class MistralAIProvider(LLMProvider):
    DEFAULT_MODEL = "mistral-medium-latest"

    def __init__(self, auth_manager: LLMAuthManager = None, model_name: str = None):
        self.auth_manager = auth_manager or LLMAuthManager()
        self._api_key = self.auth_manager.get_credentials("mistralai")
        self._tool_registry = ToolRegistry()
        self._model_name = model_name if model_name else self.DEFAULT_MODEL
        self._driver = MistralAIModelDriver("mistralai", self._model_name, self._api_key, self._tool_registry)

    def get_model_name(self) -> str:
        return self._model_name

    @property
    def driver(self):
        return self._driver

    def execute_tool(self, tool_name: str, event_bus, *args, **kwargs):
        from janito.tool_executor import ToolExecutor
        executor = ToolExecutor(registry=self._tool_registry, event_bus=event_bus)
        return executor.execute_by_name(tool_name, *args, **kwargs)

    @classmethod
    def list_models(cls):
        """
        Return a list of supported MistralAI models with table fields ("N/A" for unknowns).
        """
        model_names = [
            "mistral-medium-latest"
        ]
        fields = ["name", "context", "max_input", "max_cot", "max_response", "thinking_supported"]
        return [
            {"name": name, "context": "N/A", "max_input": "N/A", "max_cot": "N/A", "max_response": "N/A", "thinking_supported": "N/A"}
            for name in model_names
        ]

LLMProviderRegistry.register("mistralai", MistralAIProvider)
