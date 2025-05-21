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

    def __init__(self, auth_manager: LLMAuthManager = None, config: dict = None):
        self.auth_manager = auth_manager or LLMAuthManager()
        self._api_key = self.auth_manager.get_credentials(type(self).name)
        self._tool_registry = ToolRegistry()
        _config = config or {}
        if 'model_name' not in _config:
            _config['model_name'] = self.DEFAULT_MODEL
        self._info = LLMDriverConfig(
            model=_config.get('model_name', self.DEFAULT_MODEL),
            api_key=self._api_key,
            base_url=_config.get('base_url'),
            max_tokens=_config.get('max_tokens'),
            temperature=_config.get('temperature'),
            top_p=_config.get('top_p'),
            presence_penalty=_config.get('presence_penalty'),
            frequency_penalty=_config.get('frequency_penalty'),
            stop=_config.get('stop'),
            extra={k: v for k, v in _config.items() if k not in ['model_name','base_url','max_tokens','temperature','top_p','presence_penalty','frequency_penalty','stop']}
        )
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
