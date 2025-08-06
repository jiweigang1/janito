"""Cerebras Inference provider implementation."""

from typing import Dict, Any
from janito.llm.provider import LLMProvider
from janito.llm.auth import LLMAuthManager
from janito.llm.driver_config import LLMDriverConfig
from janito.drivers.openai.driver import OpenAIModelDriver
from janito.tools import get_local_tools_adapter
from janito.providers.registry import LLMProviderRegistry
from .model_info import MODEL_SPECS


class CerebrasProvider(LLMProvider):
    """Cerebras Inference API provider."""
    
    name = "cerebras"
    DEFAULT_MODEL = "gpt-oss-120b"
    MAINTAINER = "João Pinto <janito@ikignosis.org>"
    MODEL_SPECS = MODEL_SPECS

    def __init__(self, config=None, auth_manager=None):
        """Initialize Cerebras provider with optional configuration."""
        super().__init__()
        self._tools_adapter = get_local_tools_adapter()
        self._driver = None
        self.auth_manager = auth_manager
        self._driver_config = config or LLMDriverConfig(model=None)
        
        if not self.available:
            return
            
        self._initialize_config()
        self._driver_config.base_url = "https://api.cerebras.ai/v1"

    def _initialize_config(self):
        """Initialize configuration and API key."""
        auth_manager = self.auth_manager or LLMAuthManager()
        self._api_key = auth_manager.get_credentials("cerebras")
        if not self._api_key:
            from janito.llm.auth_utils import handle_missing_api_key
            handle_missing_api_key(self.name, "CEREBRAS_API_KEY")

        if not self._driver_config.model:
            self._driver_config.model = self.DEFAULT_MODEL
        if not self._driver_config.api_key:
            self._driver_config.api_key = self._api_key

        self.fill_missing_device_info(self._driver_config)

    @property
    def driver(self) -> OpenAIModelDriver:
        if not self.available:
            raise ImportError(
                f"CerebrasProvider unavailable: {self.unavailable_reason}"
            )
        return self.create_driver()

    @property
    def available(self):
        return OpenAIModelDriver.available

    @property
    def unavailable_reason(self):
        return OpenAIModelDriver.unavailable_reason

    def create_driver(self) -> OpenAIModelDriver:
        """Create and return an OpenAI-compatible Cerebras driver instance."""
        driver = OpenAIModelDriver(
            tools_adapter=self._tools_adapter, provider_name=self.name
        )
        driver.config = self._driver_config
        return driver

    @property
    def driver_config(self):
        """Return the driver configuration."""
        return self._driver_config

    def is_model_available(self, model_name: str) -> bool:
        """Check if a model is available for this provider."""
        return model_name in self.MODEL_SPECS

    def get_model_info(self, model_name: str = None) -> Dict[str, Any]:
        """Get model information for the specified model or all models."""
        if model_name is None:
            return {
                name: model_info.to_dict()
                for name, model_info in self.MODEL_SPECS.items()
            }
        
        if model_name in self.MODEL_SPECS:
            return self.MODEL_SPECS[model_name].to_dict()
        
        return None

    def execute_tool(self, tool_name: str, event_bus, *args, **kwargs):
        self._tools_adapter.event_bus = event_bus
        return self._tools_adapter.execute_by_name(tool_name, *args, **kwargs)


# Register the provider
LLMProviderRegistry.register(CerebrasProvider.name, CerebrasProvider)