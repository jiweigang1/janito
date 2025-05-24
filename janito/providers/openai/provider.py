from janito.llm.provider import LLMProvider
from janito.llm.model import LLMModelInfo
from janito.llm.auth import LLMAuthManager
from janito.llm.driver_config import LLMDriverConfig
from janito.drivers.openai.driver import OpenAIModelDriver
from janito.drivers.openai_responses.driver import OpenAIResponsesModelDriver
from janito.tools import get_local_tools_adapter
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
        self._tools_adapter = get_local_tools_adapter()
        self._driver_config = config or LLMDriverConfig(model=None)  # now called self._driver_config throughout
        if not self._driver_config.model:
            self._driver_config.model = self.DEFAULT_MODEL
        if not self._driver_config.api_key:
            self._driver_config.api_key = self._api_key
        self.fill_missing_device_info(self._driver_config)
        self._driver = OpenAIModelDriver(self._driver_config, user_prompt=None, tools_adapter=self._tools_adapter)  # self._tools_adapter is now always the shared, fully registered adapter

    def stream_generate(self, prompt_or_messages, system_prompt=None, tools=None, **kwargs):
        """Delegate streaming to the underlying OpenAIModelDriver."""
        driver = self.driver
        return driver._run_generation(
            prompt_or_messages,
            system_prompt=system_prompt,
            tools=tools,
            schemas=driver._generate_schemas(tools) if hasattr(driver, '_generate_schemas') else None,
            **kwargs
        )

    @property
    def driver(self) -> OpenAIModelDriver:
        return self._driver

    def create_agent(self, tools_adapter=None, agent_name: str = None, **kwargs):
        from janito.llm.agent import LLMAgent
        # Always create a new driver with the passed-in tools_adapter
        if tools_adapter is None:
            tools_adapter = get_local_tools_adapter()
        driver = OpenAIModelDriver(self._driver_config, user_prompt=None, tools_adapter=tools_adapter)
        return LLMAgent(driver, tools_adapter, agent_name=agent_name, **kwargs)

    def execute_tool(self, tool_name: str, event_bus, *args, **kwargs):
        self._tools_adapter.event_bus = event_bus
        return self._tools_adapter.execute_by_name(tool_name, *args, **kwargs)

LLMProviderRegistry.register(OpenAIProvider.name, OpenAIProvider)
