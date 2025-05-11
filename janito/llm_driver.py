from abc import ABC, abstractmethod
from typing import Optional

class LLMDriver(ABC):
    """
    Abstract base class for LLM drivers. Each driver represents a specific model or capability within a provider.
    """
    def __init__(self, provider_name: str, model_name: str):
        self.provider_name = provider_name
        self.model_name = model_name

    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None, functions: Optional[list] = None, **kwargs) -> str:
        """
        Generate a response from the LLM driver given a prompt.
        Args:
            prompt (str): The prompt to send to the driver.
            system_prompt (Optional[str]): An optional system prompt to guide the model's behavior.
            functions (Optional[list]): Optional list of function definitions for function calling (driver-specific).
            **kwargs: Additional driver-specific parameters.
        Returns:
            str: The generated response from the driver.
        """
        pass

    def get_name(self) -> str:
        """
        Return the full name of the driver in the format provider_name/driver_class_name/model_name.
        Returns:
            str: The driver name.
        """
        return f"{self.provider_name}/{self.model_name}"
