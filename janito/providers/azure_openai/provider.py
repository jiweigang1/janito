from janito.llm_provider import LLMProvider
from janito.llm_model_info import ModelInfo
from janito.llm_auth_manager import LLMAuthManager
from janito.tool_registry import ToolRegistry
from janito.providers.registry import LLMProviderRegistry

from .model_info import MODEL_SPECS

class AzureOpenAIProvider(LLMProvider):
    name = "azure_openai"


    MODEL_SPECS = MODEL_SPECS
    DEFAULT_MODEL = "azure-gpt-35-turbo"

    def __init__(self, config: dict = None):
        self._auth_manager = LLMAuthManager()
        self._api_key = self._auth_manager.get_credentials(type(self).name)
        self._tool_registry = ToolRegistry()
        self._params = config.copy() if config else {}
        self._model_name = self._params.get('model_name', self.DEFAULT_MODEL)
        if "api_version" not in self._params:
            self._params["api_version"] = "2023-05-15"
        self._driver = self.get_driver_for_model(config=self._params)


    @property
    def driver(self):
        return self._driver

    def execute_tool(self, tool_name: str, event_bus, *args, **kwargs):
        from janito.tool_executor import ToolExecutor
        executor = ToolExecutor(registry=self._tool_registry, event_bus=event_bus)
        return executor.execute_by_name(tool_name, *args, **kwargs)

    def get_driver_for_model(self, model_name: str, config: dict = None):
        from janito.drivers.azure_openai.driver import AzureOpenAIModelDriver
        required = getattr(AzureOpenAIModelDriver, 'required_config', None)
        if required:
            missing = [k for k in required if not config or k not in config or config.get(k) in (None, "")]
            if missing:
                raise ValueError(f"Missing required config for AzureOpenAIModelDriver: {', '.join(missing)}")
        final_config = dict(config or {})
        spec = self.get_model_info(model_name)
        if 'max_tokens' not in final_config or not final_config.get('max_tokens'):
            if spec and 'max_response' in spec and spec['max_response'] not in (None, '', 'N/A'):
                try:
                    final_config['max_tokens'] = int(spec['max_response'])
                except Exception:
                    pass
        return AzureOpenAIModelDriver(
            type(self).name,
            model_name,
            self._api_key,
            self._tool_registry,
            final_config
        )

LLMProviderRegistry.register(AzureOpenAIProvider.name, AzureOpenAIProvider)
