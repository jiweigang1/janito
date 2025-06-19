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
        super().__init__(tools_adapter=tools_adapter)
        self.azure_endpoint = None
        self.api_version = None
        self.api_key = None

    # ... rest of the implementation ...
