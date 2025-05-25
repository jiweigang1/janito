from janito.drivers.openai.driver import OpenAIModelDriver
# Safe import of AzureOpenAI SDK
try:
    from openai import AzureOpenAI
    DRIVER_AVAILABLE = True
    DRIVER_UNAVAILABLE_REASON = None
except ImportError:
    DRIVER_AVAILABLE = False
    DRIVER_UNAVAILABLE_REASON = "Missing dependency: openai (pip install openai)"
    
from janito.llm.driver_config import LLMDriverConfig

class AzureOpenAIModelDriver(OpenAIModelDriver):
    available = DRIVER_AVAILABLE
    unavailable_reason = DRIVER_UNAVAILABLE_REASON

    @classmethod
    def is_available(cls):
        return cls.available

    name = "azure_openai"
    required_config = {"base_url"}  # Update key as used in your config logic
    def __init__(self, driver_config: LLMDriverConfig, user_prompt: str = None, conversation_history=None, tools_adapter=None):
        if not self.available:
            raise ImportError(f"AzureOpenAIModelDriver unavailable: {self.unavailable_reason}")
        super().__init__(driver_config, user_prompt=user_prompt, conversation_history=conversation_history, tools_adapter=tools_adapter)
        self.azure_endpoint = driver_config.base_url
        self.api_version = getattr(driver_config, "extra", {}).get("api_version")
        self.api_key = driver_config.api_key

    def _get_max_tokens(self):
        if self.config is not None and getattr(self.config, "max_tokens", None) not in (None, '', 'N/A'):
            try:
                return int(self.config.max_tokens)
            except Exception:
                return None
        return None

    def _create_client(self):
        return AzureOpenAI(api_key=self.api_key, azure_endpoint=self.azure_endpoint, api_version=self.api_version)

    def _send_api_request(self, client, messages, schemas, **api_kwargs):
        # Set max_tokens if available
        max_tokens = self._get_max_tokens()
        if max_tokens is not None:
            api_kwargs['max_tokens'] = max_tokens
        return client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            **api_kwargs
        )
