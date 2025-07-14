from janito.llm.provider import LLMProvider
from janito.llm.auth import LLMAuthManager
from janito.llm.driver_config import LLMDriverConfig
from janito.drivers.openai.driver import OpenAIModelDriver
from janito.tools import get_local_tools_adapter
from janito.providers.registry import LLMProviderRegistry
from .model_info import MOONSHOTAI_MODEL_SPECS

class MoonshotAIProvider(LLMProvider):
    name = "moonshotai"
    maintainer = "João Pinto <lamego.pinto@gmail.com>"
    MODEL_SPECS = MOONSHOTAI_MODEL_SPECS
    DEFAULT_MODEL = "kimi-k2-0711-preview"

    def __init__(self, auth_manager: LLMAuthManager = None, config: LLMDriverConfig = None):
        if not self.available:
            self._tools_adapter = get_local_tools_adapter()
            self._driver = None
        else:
            self.auth_manager = auth_manager or LLMAuthManager()
            self._api_key = self.auth_manager.get_credentials(type(self).name)
            self._tools_adapter = get_local_tools_adapter()
            self._driver_config = config or LLMDriverConfig(model=None)
            if not self._driver_config.model:
                self._driver_config.model = self.DEFAULT_MODEL
            if not self._driver_config.api_key:
                self._driver_config.api_key = self._api_key
            # Set only the correct token parameter for the model
            model_name = self._driver_config.model
            model_spec = self.MODEL_SPECS.get(model_name)
            if hasattr(self._driver_config, "max_tokens"):
                self._driver_config.max_tokens = None
            if hasattr(self._driver_config, "max_completion_tokens"):
                self._driver_config.max_completion_tokens = None
            if model_spec:
                if getattr(model_spec, "thinking_supported", False):
                    max_cot = getattr(model_spec, "max_cot", None)
                    if max_cot and max_cot != "N/A":
                        self._driver_config.max_completion_tokens = int(max_cot)
                else:
                    max_response = getattr(model_spec, "max_response", None)
                    if max_response and max_response != "N/A":
                        self._driver_config.max_tokens = int(max_response)
            self.fill_missing_device_info(self._driver_config)
            self._driver = None
            # Set MoonshotAI base_url
            self._driver_config.base_url = "https://api.moonshot.ai/v1"

    @property
    def driver(self) -> OpenAIModelDriver:
        if not self.available:
            raise ImportError(f"MoonshotAIProvider unavailable: {self.unavailable_reason}")
        return self._driver

    @property
    def available(self):
        return OpenAIModelDriver.available

    @property
    def unavailable_reason(self):
        return OpenAIModelDriver.unavailable_reason

    def create_driver(self):
        driver = OpenAIModelDriver(
            tools_adapter=self._tools_adapter, provider_name=self.name
        )
        driver.config = self._driver_config
        return driver

    @property
    def model_name(self):
        return self._driver_config.model

    @property
    def driver_config(self):
        return self._driver_config

    def execute_tool(self, tool_name: str, event_bus, *args, **kwargs):
        self._tools_adapter.event_bus = event_bus
        return self._tools_adapter.execute_by_name(tool_name, *args, **kwargs)

LLMProviderRegistry.register(MoonshotAIProvider.name, MoonshotAIProvider)
