from typing import List, Optional
from janito.llm_provider import LLMProvider
from janito.llm_auth_manager import LLMAuthManager
from janito.providers.google_gemini.driver import GoogleGeminiModelDriver
from janito.tool_executor import ToolExecutor
from janito.providers.registry import LLMProviderRegistry

class GoogleGeminiProvider(LLMProvider):
    """
    Provider for Google Gemini LLMs via google-genai.
    Default model: 'gemini-2.5-pro-preview-05-06'.
    Available models: 'gemini-2.5-pro-preview-05-06', 'gemini-2.0-pro', 'gemini-2.0-flash-001'.
    """
    _supported_models = [
        "gemini-2.5-pro-preview-05-06",
        "gemini-2.0-pro",
        "gemini-2.0-flash-001",
    ]

    def __init__(self):
        self._auth_manager = LLMAuthManager()
        self._tool_executor = ToolExecutor()

    def get_model_name(self) -> str:
        return self._supported_models[0]  # Default: gemini-2.5-pro-preview-05-06

    def list_drivers(self, thinking_budget: int = 0) -> List[GoogleGeminiModelDriver]:
        api_key = self._auth_manager.get_credentials("google_gemini")
        return [GoogleGeminiModelDriver("google_gemini", model, api_key, self._tool_executor, thinking_budget=thinking_budget) for model in self._supported_models]

    def get_driver(self, name: str, thinking_budget: int = 0) -> GoogleGeminiModelDriver:
        if name not in self._supported_models:
            raise ValueError(f"Model '{name}' not supported.")
        api_key = self._auth_manager.get_credentials("google_gemini")
        return GoogleGeminiModelDriver("google_gemini", name, api_key, self._tool_executor, thinking_budget=thinking_budget)

    def list_supported_models(self) -> List[str]:
        return list(self._supported_models)

    def get_recommended_driver_for_model(self, model_name: str, thinking_budget: int = 0) -> GoogleGeminiModelDriver:
        return self.get_driver(model_name, thinking_budget=thinking_budget)

    def create_agent(self, system_prompt: Optional[str] = None, thinking_budget: int = 0):
        driver = self.get_driver(self.get_model_name(), thinking_budget=thinking_budget)
        from janito.llm_agent import LLMAgent
        return LLMAgent(driver, system_prompt=system_prompt)

LLMProviderRegistry.register("google_gemini", GoogleGeminiProvider)
