from janito.llm.provider import LLMProvider
from janito.llm.model import LLMModelInfo
from janito.llm.auth import LLMAuthManager
from janito.llm.driver_config import LLMDriverConfig
from janito.drivers.openai.driver import OpenAIModelDriver
from janito.drivers.openai_responses.driver import OpenAIResponsesModelDriver
from janito.tool_executor import ToolExecutor
from janito.tool_registry import ToolRegistry
from janito.providers.registry import LLMProviderRegistry

from .model_info import MODEL_SPECS

class OpenAIProvider(LLMProvider):
    name = "openai"
    maintainer = "João Pinto <lamego.pinto@gmail.com>"
    MODEL_SPECS = MODEL_SPECS
    DEFAULT_MODEL = "gpt-4.1"  # Options: gpt-4.1, gpt-4o, o3-mini, o4-mini, o4-mini-high

    def __init__(self, auth_manager: LLMAuthManager = None, config: LLMDriverConfig = None):
        self.auth_manager = auth_manager or LLMAuthManager()
        self._api_key = self.auth_manager.get_credentials(type(self).name)
        self._tool_registry = ToolRegistry()
        self._driver_config = config or LLMDriverConfig(model=None)  # now called self._driver_config throughout
        if not self._driver_config.model:
            self._driver_config.model = self.DEFAULT_MODEL
        if not self._driver_config.api_key:
            self._driver_config.api_key = self._api_key
        self.fill_missing_device_info(self._driver_config)
        self._driver = OpenAIModelDriver(self._driver_config, self._tool_registry)

    @property
    def driver(self) -> OpenAIModelDriver:
        return self._driver

    def execute_tool(self, tool_name: str, event_bus, *args, **kwargs):
        executor = ToolExecutor(registry=self._tool_registry, event_bus=event_bus)
        return executor.execute_by_name(tool_name, *args, **kwargs)

LLMProviderRegistry.register(OpenAIProvider.name, OpenAIProvider)
