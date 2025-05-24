from janito.llm.provider import LLMProvider
from janito.llm.model import LLMModelInfo
from janito.llm.auth import LLMAuthManager
from janito.llm.driver_config import LLMDriverConfig
from janito.tools.adapters.local.adapter import LocalToolsAdapter
from janito.providers.registry import LLMProviderRegistry

from .model_info import MODEL_SPECS

class AnthropicProvider(LLMProvider):
    name = "anthropic"
    maintainer = "Needs maintainer"
    MODEL_SPECS = MODEL_SPECS
    DEFAULT_MODEL = "claude-3-opus-20240229"

    def __init__(self, auth_manager: LLMAuthManager = None, config: LLMDriverConfig = None):
        self.auth_manager = auth_manager or LLMAuthManager()
        self._api_key = self.auth_manager.get_credentials(type(self).name)
        self._tools_adapter = LocalToolsAdapter()
        self._info = config or LLMDriverConfig(model=None)
        if not self._info.model:
            self._info.model = self.DEFAULT_MODEL
        if not self._info.api_key:
            self._info.api_key = self._api_key
        self.fill_missing_device_info(self._info)
        from janito.drivers.anthropic.driver import AnthropicModelDriver
        self._driver = AnthropicModelDriver(self._info, self._tools_adapter)

    @property
    def driver(self):
        return self._driver

    def create_agent(self, tools_adapter=None, agent_name: str = None, **kwargs):
        from janito.llm.agent import LLMAgent
        from janito.drivers.anthropic.driver import AnthropicModelDriver
        # Always create a new driver with the passed-in tools_adapter
        driver = AnthropicModelDriver(self._info, None if tools_adapter is None else tools_adapter)
        return LLMAgent(driver, tools_adapter, agent_name=agent_name, **kwargs)

LLMProviderRegistry.register(AnthropicProvider.name, AnthropicProvider)
