from janito.llm.provider import LLMProvider
from janito.llm.model import LLMModelInfo
from janito.llm.auth import LLMAuthManager
from janito.llm.driver_config import LLMDriverConfig
from janito.tool_registry import ToolRegistry
from janito.providers.registry import LLMProviderRegistry

from .model_info import MODEL_SPECS

class AzureOpenAIProvider(LLMProvider):
    name = "azure_openai"
    MODEL_SPECS = MODEL_SPECS
    DEFAULT_MODEL = "azure-gpt-35-turbo"

    def __init__(self, auth_manager: LLMAuthManager = None, config: LLMDriverConfig = None):
        self._auth_manager = auth_manager or LLMAuthManager()
        self._api_key = self._auth_manager.get_credentials(type(self).name)
        self._tool_registry = ToolRegistry()
        self._info = config or LLMDriverConfig(model=None)
        if not self._info.model:
            self._info.model = self.DEFAULT_MODEL
        if not self._info.api_key:
            self._info.api_key = self._api_key
        if not getattr(self._info, 'extra', None):
            if getattr(self._info, 'api_version', None) is None:
                self._info.api_version = "2023-05-15"
        self.fill_missing_device_info(self._info)
        from janito.drivers.azure_openai.driver import AzureOpenAIModelDriver
        self._driver = AzureOpenAIModelDriver(self._info, self._tool_registry)


    @property
    def driver(self):
        return self._driver

    def execute_tool(self, tool_name: str, event_bus, *args, **kwargs):
        from janito.tool_executor import ToolExecutor
        executor = ToolExecutor(registry=self._tool_registry, event_bus=event_bus)
        return executor.execute_by_name(tool_name, *args, **kwargs)

    def get_driver_for_model(self, config: dict = None):
        from janito.drivers.azure_openai.driver import AzureOpenAIModelDriver
        required = getattr(AzureOpenAIModelDriver, 'required_config', None)
        if required:
            missing = [k for k in required if not config or k not in config or config.get(k) in (None, "")]
            if missing:
                raise ValueError(f"Missing required config for AzureOpenAIModelDriver: {', '.join(missing)}")
        from janito.llm.driver_config_builder import build_llm_driver_config
        llm_driver_config = build_llm_driver_config(config or {}, AzureOpenAIModelDriver)
        return AzureOpenAIModelDriver(
            llm_driver_config,
            self._tool_registry
        )

LLMProviderRegistry.register(AzureOpenAIProvider.name, AzureOpenAIProvider)
