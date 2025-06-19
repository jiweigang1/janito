from janito.llm.provider import LLMProvider
from janito.llm.model import LLMModelInfo
from janito.llm.auth import LLMAuthManager
from janito.llm.driver_config import LLMDriverConfig
from janito.tools.adapters.local.adapter import LocalToolsAdapter
from janito.providers.registry import LLMProviderRegistry

from .model_info import MODEL_SPECS

from janito.drivers.azure_openai.driver import AzureOpenAIModelDriver

available = AzureOpenAIModelDriver.available
unavailable_reason = AzureOpenAIModelDriver.unavailable_reason
maintainer = "João Pinto <lamego.pinto@gmail.com>"


class AzureOpenAIProvider(LLMProvider):
    name = "azure_openai"
    maintainer = "João Pinto <lamego.pinto@gmail.com>"
    MODEL_SPECS = MODEL_SPECS
    DEFAULT_MODEL = "azure_openai_deployment"

    def __init__(
        self, auth_manager: LLMAuthManager = None, config: LLMDriverConfig = None
    ):
        if not self.available:
            self._driver = None
            return
        self._auth_manager = auth_manager or LLMAuthManager()
        self._api_key = self._auth_manager.get_credentials(type(self).name)
        self._tools_adapter = LocalToolsAdapter()
        self._driver_config = config or LLMDriverConfig(model=None)
        if not self._driver_config.model:
            self._driver_config.model = self.DEFAULT_MODEL
        if not self._driver_config.api_key:
            self._driver_config.api_key = self._api_key
        if not self._driver_config.extra.get("api_version"):
            self._driver_config.extra["api_version"] = "2023-05-15"
        self.fill_missing_device_info(self._driver_config)
        self._driver = AzureOpenAIModelDriver(tools_adapter=self._tools_adapter)

    @property
    def driver(self):
        if not self.available:
            raise ImportError(
                f"AzureOpenAIProvider unavailable: {self.unavailable_reason}"
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
        from janito.drivers.azure_openai.driver import AzureOpenAIModelDriver

        # Always create a new driver with the passed-in tools_adapter
        driver = AzureOpenAIModelDriver(tools_adapter=tools_adapter)
        return LLMAgent(self, tools_adapter, agent_name=agent_name, **kwargs)

    def execute_tool(self, tool_name: str, event_bus, *args, **kwargs):
        # Use direct execution via adapter:
        self._tools_adapter.event_bus = event_bus
        return self._tools_adapter.execute_by_name(tool_name, *args, **kwargs)


LLMProviderRegistry.register(AzureOpenAIProvider.name, AzureOpenAIProvider)
