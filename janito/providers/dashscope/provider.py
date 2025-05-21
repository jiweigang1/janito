from janito.llm.provider import LLMProvider
from janito.llm.model import LLMModelInfo
from janito.llm.auth import LLMAuthManager
from janito.llm.driver_config import LLMDriverConfig
from janito.drivers.dashscope.driver import DashScopeModelDriver
from janito.tool_executor import ToolExecutor
from janito.tool_registry import ToolRegistry
from janito.providers.registry import LLMProviderRegistry

from .model_info import MODEL_SPECS

class DashScopeProvider(LLMProvider):
    MODEL_SPECS = MODEL_SPECS
    name = "dashscope"
    DEFAULT_MODEL = "qwen3-235b-a22b"

    def __init__(self, config: LLMDriverConfig = None):
        self.auth_manager = LLMAuthManager()
        self._api_key = self.auth_manager.get_credentials(type(self).name)
        self._tool_registry = ToolRegistry()
        self._info = config or LLMDriverConfig(model=None)
        if not self._info.model:
            self._info.model = self.DEFAULT_MODEL
        if not self._info.api_key:
            self._info.api_key = self._api_key
        from janito.drivers.dashscope.driver import DashScopeModelDriver
        self.fill_missing_device_info(self._info)
        self._driver = DashScopeModelDriver(self._info, self._tool_registry)

    @property
    def driver(self) -> DashScopeModelDriver:
        return self._driver

    def create_agent(self, agent_name: str = None, **kwargs):
        from janito.llm.agent import LLMAgent
        return Agent(self.driver, agent_name=agent_name, **kwargs)

    def execute_tool(self, tool_name: str, event_bus, *args, **kwargs):
        executor = ToolExecutor(registry=self._tool_registry, event_bus=event_bus)
        return executor.execute_by_name(tool_name, *args, **kwargs)

LLMProviderRegistry.register(DashScopeProvider.name, DashScopeProvider)
