# janito/drivers/driver_registry.py
"""
DriverRegistry: Maps driver string names to class objects for use by providers.
"""

from typing import Dict, Type

# --- Import driver classes ---
from janito.drivers.azure_openai.driver import AzureOpenAIModelDriver
from janito.drivers.openai.driver import OpenAIModelDriver

_DRIVER_REGISTRY: Dict[str, Type] = {
    "AzureOpenAIModelDriver": AzureOpenAIModelDriver,
    "OpenAIModelDriver": OpenAIModelDriver,
}


def get_driver_class(name: str):
    """Get the driver class by string name."""
    try:
        return _DRIVER_REGISTRY[name]
    except KeyError:
        raise ValueError(f"No driver found for name: {name}")


def register_driver(name: str, cls: type):
    _DRIVER_REGISTRY[name] = cls
