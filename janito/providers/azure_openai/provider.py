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

    def __init__(self, config: dict = None):
        self._auth_manager = LLMAuthManager()
        self._api_key = self._auth_manager.get_credentials(type(self).name)
        self._tool_registry = ToolRegistry()
        _params = config.copy() if config else {}
        _model_name = _params.get('model_name', self.DEFAULT_MODEL)
        if "api_version" not in _params:
            _params["api_version"] = "2023-05-15"
        # Build driver info
        self._info = LLMDriverConfig(
            model=_model_name,
            api_key=self._api_key,
            base_url=_params.get("base_url"),
            max_tokens=_params.get("max_tokens"),
            temperature=_params.get("temperature"),
            top_p=_params.get("top_p"),
            presence_penalty=_params.get("presence_penalty"),
            frequency_penalty=_params.get("frequency_penalty"),
            stop=_params.get("stop"),
            extra={k: v for k, v in _params.items() if k not in ['model_name','base_url','max_tokens','temperature','top_p','presence_penalty','frequency_penalty','stop']}
        )
        from janito.drivers.azure_openai.driver import AzureOpenAIModelDriver
        self._driver = AzureOpenAIModelDriver(self._info, self._tool_registry)


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
