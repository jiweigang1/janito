from janito.llm_provider import LLMProvider
from janito.llm_auth_manager import LLMAuthManager
from janito.drivers.dashscope.driver import DashScopeModelDriver
from janito.tool_executor import ToolExecutor
from janito.tool_registry import ToolRegistry
from janito.providers.registry import LLMProviderRegistry

class DashScopeProvider(LLMProvider):
    DEFAULT_MODEL = "qwen3-235b-a22b"

    # Model specifications with detailed metadata
    MODEL_SPECS = {
        # Commercial models with minimal info
        "qwen-max": {
            "context": 32768,
            "max_input": 30720,
            "max_cot": None,
            "max_response": 8192,
            "thinking_supported": False,
            "open": False,
            "default_temp": 0.2
        },
        "qwen-plus": {
            "context": 131072,
            "max_input": 129024,
            "max_cot": None,
            "max_response": 8192,
            "thinking_supported": False,
            "open": False,
            "default_temp": 0.2
        },
        "qwen-turbo": {
            "context": 1008192,
            "max_input": 1000000,
            "max_cot": None,
            "max_response": 8192,
            "thinking_supported": False,
            "open": False,
            "default_temp": 0.2
        },
        "qwen-plus-2025-04-28": {
            "context": 131072,
            "max_input": 129024,
            "max_cot": 38912,
            "max_response": 16384,
            "thinking_supported": True,
            "open": False,
            "default_temp": 0.2
        },
        "qwen-turbo-2025-04-28": {
            "context": [1000000, 131072],
            "max_input": [1000000, 129024],
            "max_cot": 38912,
            "max_response": 8192,
            "thinking_supported": True,
            "open": False,
            "default_temp": 0.2
        },
        # Detailed models
        "qwen3-235b-a22b": {
            "context": 131072,
            "max_input": 129024,
            "max_cot": 38912,
            "max_response": 16384,
            "thinking_supported": True,
            "open": True,
            "default_temp": 0.2
        },
        "qwen3-32b": {
            "context": 131072,
            "max_input": 129024,
            "max_cot": 38912,
            "max_response": 16384,
            "thinking_supported": True,
            "open": True,
            "default_temp": 0.2
        },
        "qwen3-30b-a3b": {
            "context": 131072,
            "max_input": 129024,
            "max_cot": 38912,
            "max_response": 16384,
            "thinking_supported": True,
            "open": True,
            "default_temp": 0.2
        },
        "qwen3-14b": {
            "context": 131072,
            "max_input": 129024,
            "max_cot": 38912,
            "max_response": 8192,
            "thinking_supported": True,
            "open": True,
            "default_temp": 0.2
        },
        "qwen3-8b": {
            "context": 131072,
            "max_input": 129024,
            "max_cot": 38912,
            "max_response": 8192,
            "thinking_supported": True,
            "open": True,
            "default_temp": 0.2
        },
        "qwen3-4b": {
            "context": 131072,
            "max_input": 129024,
            "max_cot": 38912,
            "max_response": 8192,
            "thinking_supported": True,
            "open": True,
            "default_temp": 0.2
        },
        "qwen3-1.7b": {
            "context": 32768,
            "max_input": [30720, 28672],
            "max_cot": 30720,
            "max_response": 8192,
            "thinking_supported": True,
            "open": True,
            "default_temp": 0.2
        },
        "qwen3-0.6b": {
            "context": 30720,
            "max_input": [30720, 28672],
            "max_cot": 30720,
            "max_response": 8192,
            "thinking_supported": True,
            "open": True,
            "default_temp": 0.2
        },
    }

    @classmethod
    def list_models(cls, details=False):
        """
        Return a list of supported DashScope models. Each model dict includes all metadata fields, an 'open' flag, and a 'type' field ('commercial' or 'open').
        Missing values are filled with 'N/A'.
        """
        fields = ["name", "context", "max_input", "max_cot", "max_response", "thinking_supported", "open"]
        models = []
        for name, spec in cls.MODEL_SPECS.items():
            model_info = {"name": name}
            for field in fields[1:]:
                val = spec.get(field, None)
                # If thinking_supported is False, show max_cot as '-'
                if field == "max_cot" and spec.get("thinking_supported") is False:
                    model_info[field] = "-"
                elif field == "open":
                    model_info[field] = "Open" if val is True else "Proprietary"
                else:
                    model_info[field] = val if val is not None else "N/A"
            # Add category field: 'Open' if open is True, else 'Proprietary'
            model_info["category"] = "Open" if model_info.get("open") is True else "Proprietary"
            # Add default_temp field
            model_info["default_temp"] = spec.get("default_temp", 0.2)
            models.append(model_info)
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
