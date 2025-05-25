# janito/drivers/driver_registry.py
"""
DriverRegistry: Maps driver string names to class objects for use by providers.
"""

from typing import Dict, Type

# --- Import driver classes ---
from janito.drivers.anthropic.driver import AnthropicModelDriver
from janito.drivers.azure_openai.driver import AzureOpenAIModelDriver
from janito.drivers.dashscope.driver import DashScopeModelDriver
from janito.drivers.google_genai.driver import GoogleGenaiModelDriver
from janito.drivers.mistralai.driver import MistralAIModelDriver
from janito.drivers.openai.driver import OpenAIModelDriver
from janito.drivers.openai_responses.driver import OpenAIResponsesModelDriver

_DRIVER_REGISTRY: Dict[str, Type] = {
    "AnthropicModelDriver": AnthropicModelDriver,
    "AzureOpenAIModelDriver": AzureOpenAIModelDriver,
    "DashScopeModelDriver": DashScopeModelDriver,
    "GoogleGenaiModelDriver": GoogleGenaiModelDriver,
    "MistralAIModelDriver": MistralAIModelDriver,
    "OpenAIModelDriver": OpenAIModelDriver,
    "OpenAIResponsesModelDriver": OpenAIResponsesModelDriver,
}

def get_driver_class(name: str):
    """Get the driver class by string name."""
    try:
        return _DRIVER_REGISTRY[name]
    except KeyError:
        raise ValueError(f"No driver found for name: {name}")


def register_driver(name: str, cls: type):
    _DRIVER_REGISTRY[name] = cls
