from janito.llm_provider import LLMProvider
from janito.llm_auth_manager import LLMAuthManager
from janito.drivers.google_genai.driver import GoogleGenaiModelDriver
from janito.tool_executor import ToolExecutor
from janito.providers.registry import LLMProviderRegistry

class GoogleProvider(LLMProvider):
    """
    Provider for Google LLMs via google-google.
    Default model: 'gemini-2.5-pro-preview-05-06'.
    """
    DEFAULT_MODEL = "gemini-2.5-pro-preview-05-06"

    def __init__(self):
        self._auth_manager = LLMAuthManager()
        self._tool_executor = ToolExecutor()
        self._api_key = self._auth_manager.get_credentials("google")
        self._driver = GoogleGenaiModelDriver(
            "google",
            self.DEFAULT_MODEL,
            self._api_key,
            self._tool_executor
        )

    def get_model_name(self) -> str:
        return self.DEFAULT_MODEL

    @property
    def driver(self) -> GoogleGenaiModelDriver:
        return self._driver

    def execute_tool(self, tool_name: str, *args, **kwargs):
        executor = ToolExecutor()
        return executor.execute_by_name(tool_name, *args, **kwargs)

LLMProviderRegistry.register("google", GoogleProvider)
