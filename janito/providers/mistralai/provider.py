from janito.llm.provider import LLMProvider
from janito.llm.model import LLMModelInfo
from janito.llm.auth import LLMAuthManager
from janito.llm.driver_config import LLMDriverConfig
from janito.drivers.mistralai.driver import MistralAIModelDriver
from janito.tools.adapters.local.adapter import LocalToolsAdapter
from janito.providers.registry import LLMProviderRegistry

from .model_info import MODEL_SPECS

from janito.drivers.mistralai.driver import MistralAIModelDriver

available = MistralAIModelDriver.available
unavailable_reason = MistralAIModelDriver.unavailable_reason


class MistralAIProvider(LLMProvider):
    MODEL_SPECS = MODEL_SPECS
    name = "mistralai"
    maintainer = "Needs maintainer"

    DEFAULT_MODEL = "mistral-medium-latest"

    def __init__(
        self, config: LLMDriverConfig = None, auth_manager: LLMAuthManager = None
    ):
        if not self.available:
            self._driver = None
            return
        self.auth_manager = auth_manager or LLMAuthManager()
        self._api_key = self.auth_manager.get_credentials(type(self).name)
        self._tools_adapter = LocalToolsAdapter()
        self._info = config or LLMDriverConfig(model=None)
        if not self._info.model:
            self._info.model = self.DEFAULT_MODEL
        if not self._info.api_key:
            self._info.api_key = self._api_key
        self.fill_missing_device_info(self._info)
        self._driver = MistralAIModelDriver(tools_adapter=self._tools_adapter)

    @property
    def driver(self):
        if not self.available:
            raise ImportError(
                f"MistralAIProvider unavailable: {self.unavailable_reason}"
            )
        return self._driver

    @property
    def available(self):
        return available

    @property
    def unavailable_reason(self):
        return unavailable_reason

    def create_agent(self, tools_adapter=None, agent_name: str = None, **kwargs):
        from janito.llm.agent import LLMAgent

        # Always create a new driver with the passed-in tools_adapter
        driver = MistralAIModelDriver(tools_adapter=tools_adapter)
        return LLMAgent(self, tools_adapter, agent_name=agent_name, **kwargs)

    def execute_tool(self, tool_name: str, event_bus, *args, **kwargs):
        self._tools_adapter.event_bus = event_bus
        return self._tools_adapter.execute_by_name(tool_name, *args, **kwargs)


LLMProviderRegistry.register(MistralAIProvider.name, MistralAIProvider)
