from janito.llm.provider import LLMProvider
from janito.llm.model import LLMModelInfo
from janito.llm.auth import LLMAuthManager
from janito.llm.driver_config import LLMDriverConfig
from janito.tools import get_local_tools_adapter
from janito.providers.registry import LLMProviderRegistry

from .model_info import MODEL_SPECS

from janito.drivers.anthropic.driver import AnthropicModelDriver

available = AnthropicModelDriver.available
unavailable_reason = AnthropicModelDriver.unavailable_reason
maintainer = "Needs maintainer"


class AnthropicProvider(LLMProvider):
    name = "anthropic"
    maintainer = "Needs maintainer"
    MODEL_SPECS = MODEL_SPECS
    DEFAULT_MODEL = "claude-3-opus-20240229"

    def __init__(
        self, auth_manager: LLMAuthManager = None, config: LLMDriverConfig = None
    ):
        # Ensure we always have a tools adapter, even if the driver itself is unavailable.
        self._tools_adapter = get_local_tools_adapter()
        if not self.available:
            self._driver = None
            return
        self.auth_manager = auth_manager or LLMAuthManager()
        self._api_key = self.auth_manager.get_credentials(type(self).name)
        self._tools_adapter = get_local_tools_adapter()
        self._info = config or LLMDriverConfig(model=None)
        if not self._info.model:
            self._info.model = self.DEFAULT_MODEL
        if not self._info.api_key:
            self._info.api_key = self._api_key
        self.fill_missing_device_info(self._info)
        self._driver = AnthropicModelDriver(tools_adapter=self._tools_adapter)

    @property
    def driver(self):
        if not self.available:
            raise ImportError(
                f"AnthropicProvider unavailable: {self.unavailable_reason}"
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
        from janito.drivers.anthropic.driver import AnthropicModelDriver

        # Always create a new driver with the passed-in tools_adapter
        driver = AnthropicModelDriver(tools_adapter=tools_adapter)
        return LLMAgent(self, tools_adapter, agent_name=agent_name, **kwargs)


LLMProviderRegistry.register(AnthropicProvider.name, AnthropicProvider)
