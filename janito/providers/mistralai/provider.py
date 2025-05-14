from janito.llm_provider import LLMProvider
from janito.llm_auth_manager import LLMAuthManager
from janito.drivers.mistralai.driver import MistralAIModelDriver
from janito.tool_executor import ToolExecutor
from janito.providers.registry import LLMProviderRegistry

class MistralAIProvider(LLMProvider):
    DEFAULT_MODEL = "mistral-medium-latest"

    def __init__(self, auth_manager: LLMAuthManager = None):
        self.auth_manager = auth_manager or LLMAuthManager()
        self._api_key = self.auth_manager.get_credentials("mistralai")
        self._tool_executor = ToolExecutor()
        # TODO: Replace with actual driver once implemented
        self._driver = MistralAIModelDriver("mistralai", self.DEFAULT_MODEL, self._api_key, self._tool_executor)

    def get_model_name(self) -> str:
        return self.DEFAULT_MODEL

    @property
    def driver(self):
        return self._driver

    def execute_tool(self, tool_name: str, *args, **kwargs):
        executor = ToolExecutor()
        return executor.execute_by_name(tool_name, *args, **kwargs)

LLMProviderRegistry.register("mistralai", MistralAIProvider)
