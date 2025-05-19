from janito.drivers.openai.driver import OpenAIModelDriver

class AzureOpenAIModelDriver(OpenAIModelDriver):
    def __init__(self, provider_name: str, model_name: str, api_key: str, tool_registry=None, config: dict = None):
        # For Azure, api_key typically = key, and endpoint must be provided (use variable or auth manager)
        super().__init__(provider_name, model_name, api_key, tool_registry, config)
        # Example: self.endpoint = config.get('endpoint') or os.environ.get('AZURE_OPENAI_ENDPOINT')

    def _send_api_request(self, client, messages, schemas, **api_kwargs):
        # Here Azure-specific params from self.params could be attached
        return super()._send_api_request(client, messages, schemas, **api_kwargs)
