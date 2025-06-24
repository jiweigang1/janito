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

    required_config = {"base_url"}  # Update key as used in your config logic

    def __init__(self, tools_adapter=None):
        if not self.available:
            raise ImportError(
                f"AzureOpenAIModelDriver unavailable: {self.unavailable_reason}"
            )
        # Do NOT call super().__init__ if Azure SDK is not available
        OpenAIModelDriver.__init__(self, tools_adapter=tools_adapter)
        self.azure_endpoint = None
        self.api_version = None
        self.api_key = None

    def _instantiate_openai_client(self, config):
        try:
            from openai import AzureOpenAI
            api_key_display = str(config.api_key)
            if api_key_display and len(api_key_display) > 8:
                api_key_display = api_key_display[:4] + "..." + api_key_display[-4:]
            client_kwargs = {
                "api_key": config.api_key,
                "azure_endpoint": getattr(config, "base_url", None),
                "api_version": config.extra.get("api_version", "2023-05-15"),
            }
            client = AzureOpenAI(**client_kwargs)
            return client
        except Exception as e:
            print(f"[ERROR] Exception during AzureOpenAI client instantiation: {e}", flush=True)
            import traceback
            print(traceback.format_exc(), flush=True)
            raise

    def _prepare_api_kwargs(self, config, conversation):
        """
        Prepares API kwargs for Azure OpenAI, using 'model' directly (no deployment_name remapping).
        """
        api_kwargs = super()._prepare_api_kwargs(config, conversation)
        # Use 'model' as-is, matching OpenAI driver/provider behavior
        return api_kwargs

