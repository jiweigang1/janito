from janito.llm_provider import LLMProvider
from janito.llm_auth_manager import LLMAuthManager
from janito.drivers.google_genai.driver import GoogleGenaiModelDriver
from janito.tool_registry import ToolRegistry
from janito.providers.registry import LLMProviderRegistry

class GoogleProvider(LLMProvider):
    """
    Provider for Google LLMs via google-google.
    Default model: 'gemini-2.5-pro-preview-05-06'.
    """
    DEFAULT_MODEL = "gemini-2.5-pro-preview-05-06"

    @classmethod
    def list_models(cls):
        """
        Return a list of supported Google models with table fields ("N/A" for unknowns).
        """
        model_names = [
            "gemini-2.5-pro-preview-05-06"
        ]
        fields = ["name", "context", "max_input", "max_cot", "max_response", "thinking_supported"]
        return [
            {"name": name, "context": "N/A", "max_input": "N/A", "max_cot": "N/A", "max_response": "N/A", "thinking_supported": "N/A", "default_temp": 0.2}
            for name in model_names
        ]

    def __init__(self, model_name: str = None):
        self._auth_manager = LLMAuthManager()
        self._api_key = self._auth_manager.get_credentials("google")
        self._tool_registry = ToolRegistry()
        self._model_name = model_name if model_name else self.DEFAULT_MODEL
        self._driver = GoogleGenaiModelDriver(
            "google",
            self._model_name,
            self._api_key,
            self._tool_registry
        )

    def get_model_name(self) -> str:
        return self._model_name

    @property
    def driver(self) -> GoogleGenaiModelDriver:
        return self._driver

    def execute_tool(self, tool_name: str, event_bus, *args, **kwargs):
        from janito.tool_executor import ToolExecutor
        executor = ToolExecutor(registry=self._tool_registry, event_bus=event_bus)
        return executor.execute_by_name(tool_name, *args, **kwargs)

LLMProviderRegistry.register("google", GoogleProvider)
