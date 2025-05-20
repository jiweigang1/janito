from janito.drivers.openai.driver import OpenAIModelDriver
from openai import AzureOpenAI
    
from janito.llm.driver_info import LLMDriverInfo

class AzureOpenAIModelDriver(OpenAIModelDriver):
    name = "azure_openai"
    required_config = {"azure_endpoint"}  # Update key as used in your config logic
    def __init__(self, info: LLMDriverInfo, tool_registry=None):
        super().__init__(info, tool_registry)
        self.azure_endpoint = getattr(info, "extra", {}).get("azure_endpoint")
        self.api_version = getattr(info, "extra", {}).get("api_version")
        self.api_key = info.api_key

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
