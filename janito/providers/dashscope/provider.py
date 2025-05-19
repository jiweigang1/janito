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


    @classmethod
    def list_models(cls, details=False):
        """
        Return a list of supported DashScope models using ModelInfo dataclass for structured output.
        """
        fields = ["context", "max_input", "max_cot", "max_response", "thinking_supported", "open", "category", "default_temp"]
        models = []
        for name, spec in cls.MODEL_SPECS.items():
            # Compose arguments for dataclass
            model_kwargs = {"name": name}
            for field in fields:
                if field in spec:
                    model_kwargs[field] = spec[field]
                elif field == "max_cot" and spec.get("thinking_supported") is False:
                    model_kwargs[field] = "-"
                else:
                    model_kwargs[field] = spec.get(field, "N/A")
            # Default temp special case
            if "default_temp" not in model_kwargs:
                model_kwargs["default_temp"] = 0.2
            models.append(ModelInfo(**model_kwargs).to_dict())
        return models

    @classmethod
    def get_model_info(cls, model_name):
        """
        Return the metadata dictionary for a given model name, or None if not found.
        """
        return cls.MODEL_SPECS.get(model_name)

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
