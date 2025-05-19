from janito.llm_provider import LLMProvider
from janito.llm_model_info import ModelInfo
from janito.llm_auth_manager import LLMAuthManager
from janito.drivers.dashscope.driver import DashScopeModelDriver
from janito.tool_executor import ToolExecutor
from janito.tool_registry import ToolRegistry
from janito.providers.registry import LLMProviderRegistry

from .model_info import MODEL_SPECS

class DashScopeProvider(LLMProvider):
    DEFAULT_MODEL = "qwen3-235b-a22b"



    def __init__(self, auth_manager: LLMAuthManager = None, model_name: str = None):
        self.auth_manager = auth_manager or LLMAuthManager()
        self._api_key = self.auth_manager.get_credentials("dashscope")
        self._tool_registry = ToolRegistry()
        self._model_name = model_name if model_name else self.DEFAULT_MODEL
        self._driver = DashScopeModelDriver("dashscope", self._model_name, self._api_key, self._tool_registry)

    def get_model_name(self) -> str:
        return self._model_name

    @property
    def driver(self) -> DashScopeModelDriver:
        return self._driver

    def create_agent(self, agent_name: str = None, **kwargs):
        """
        Create an Agent for DashScope.
        Args:
            agent_name (str): Optional agent name.
            **kwargs: Additional parameters for the agent.
        Returns:
            Agent: An instance of Agent configured with the appropriate driver.
        """
        from janito.agent.agent import Agent
        return Agent(self.driver, agent_name=agent_name, **kwargs)

    def execute_tool(self, tool_name: str, event_bus, *args, **kwargs):
        executor = ToolExecutor(registry=self._tool_registry, event_bus=event_bus)
        return executor.execute_by_name(tool_name, *args, **kwargs)

LLMProviderRegistry.register("dashscope", DashScopeProvider)
