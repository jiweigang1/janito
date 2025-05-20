from janito.drivers.openai.driver import OpenAIModelDriver
from openai import AzureOpenAI
    
class AzureOpenAIModelDriver(OpenAIModelDriver):
    def _get_max_tokens(self):
        if self.config is not None:
            mt = self.config.get("max_tokens")
            if mt not in (None, '', 'N/A'):
                try:
                    return int(mt)
                except Exception:
                    return None
        return None

    required_config = {"azure_endpoint"}  # Update key as used in your config logic
    def __init__(self, provider_name: str, model_name: str, api_key: str, tool_registry=None, config: dict = None):
        super().__init__(provider_name, model_name, api_key, tool_registry, config)
        self.azure_endpoint = config.get("azure_endpoint") if config else None
        self.api_version = config.get("api_version") if config else None
        self.api_key = api_key

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
