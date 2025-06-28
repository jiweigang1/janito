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
    def start(self, *args, **kwargs):
        # Ensure azure_deployment_name is set before starting
        config = getattr(self, 'config', None)
        deployment_name = None
        if config and hasattr(config, 'extra'):
            deployment_name = config.extra.get('azure_deployment_name')
        if not deployment_name:
            raise RuntimeError("AzureOpenAIModelDriver requires 'azure_deployment_name' to be set in config.extra['azure_deployment_name'] before starting.")
        # Call parent start if exists
        if hasattr(super(), 'start'):
            return super().start(*args, **kwargs)

    available = DRIVER_AVAILABLE
    unavailable_reason = DRIVER_UNAVAILABLE_REASON

    @classmethod
    def is_available(cls):
        return cls.available

    required_config = {"base_url"}  # Update key as used in your config logic

    def __init__(self, tools_adapter=None, provider_name=None):
        if not self.available:
            raise ImportError(
                f"AzureOpenAIModelDriver unavailable: {self.unavailable_reason}"
            )
        # Ensure proper parent initialization
        super().__init__(tools_adapter=tools_adapter, provider_name=provider_name)
        self.azure_endpoint = None
        self.api_version = None
        self.api_key = None

    def _prepare_api_kwargs(self, config, conversation):
        """
        Prepares API kwargs for Azure OpenAI, using the deployment name as the model parameter.
        Also ensures tool schemas are included if tools_adapter is present.
        """
        api_kwargs = super()._prepare_api_kwargs(config, conversation)
        deployment_name = config.extra.get("azure_deployment_name") if hasattr(config, "extra") else None
        if deployment_name:
            api_kwargs["model"] = deployment_name
        # Patch: Ensure tools are included for Azure as for OpenAI
        if self.tools_adapter:
            try:
                from janito.providers.openai.schema_generator import generate_tool_schemas
                tool_classes = self.tools_adapter.get_tool_classes()
                tool_schemas = generate_tool_schemas(tool_classes)
                api_kwargs["tools"] = tool_schemas
            except Exception as e:
                api_kwargs["tools"] = []
                if hasattr(config, "verbose_api") and config.verbose_api:
                    print(f"[AzureOpenAIModelDriver] Tool schema generation failed: {e}")
        return api_kwargs

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
            # Do NOT pass azure_deployment; deployment name is used as the 'model' param in API calls
            client = AzureOpenAI(**client_kwargs)
            return client
        except Exception as e:
            print(f"[ERROR] Exception during AzureOpenAI client instantiation: {e}", flush=True)
            import traceback
            print(traceback.format_exc(), flush=True)
            raise

