from typing import List, Optional
from janito.llm_provider import LLMProvider
from janito.llm_auth_manager import LLMAuthManager
from janito.providers.openai.driver import OpenAIModelDriver
from janito.tool_executor import ToolExecutor
from janito.providers.registry import LLMProviderRegistry

class OpenAIProvider(LLMProvider):
    DEFAULT_MODEL = "gpt-4.1"

    def __init__(self, auth_manager: LLMAuthManager = None):
        self.auth_manager = auth_manager or LLMAuthManager()
        self._api_key = self.auth_manager.get_credentials("openai")
        self._tool_executor = ToolExecutor()
        self._drivers = {
            self.DEFAULT_MODEL: OpenAIModelDriver("openai", self.DEFAULT_MODEL, self._api_key, self._tool_executor)
        }

    def get_model_name(self) -> str:
        return self.DEFAULT_MODEL

    def list_drivers(self) -> List[OpenAIModelDriver]:
        return list(self._drivers.values())

    def get_driver(self, name: str) -> OpenAIModelDriver:
        if name in self._drivers:
            return self._drivers[name]
        raise ValueError(f"Driver '{name}' not found.")

    def list_supported_models(self) -> List[str]:
        return list(self._drivers.keys())

    def get_recommended_driver_for_model(self, model_name: str) -> OpenAIModelDriver:
        if model_name in self._drivers:
            return self._drivers[model_name]
        raise ValueError(f"Model '{model_name}' not supported.")

    def execute_tool(self, tool_name: str, *args, **kwargs):
        executor = ToolExecutor()
        return executor.execute_by_name(tool_name, *args, **kwargs)

LLMProviderRegistry.register("openai", OpenAIProvider)
