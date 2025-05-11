from abc import ABC, abstractmethod
from typing import List
from janito.llm_driver import LLMDriver

class LLMProvider(ABC):
    """
    Abstract base class for Large Language Model (LLM) providers.
    Each provider manages one or more LLMDrivers (models or capabilities).
    Subclasses should implement the core interface for interacting with LLM APIs.
    """

    @abstractmethod
    def get_model_name(self) -> str:
        """
        Return the name of the model used by this provider.
        Returns:
            str: The model name.
        """
        pass

    @abstractmethod
    def list_drivers(self) -> List[LLMDriver]:
        """
        List all drivers supported by this provider.
        Returns:
            List[LLMDriver]: List of driver instances.
        """
        pass

    @abstractmethod
    def get_driver(self, name: str) -> LLMDriver:
        """
        Retrieve a specific driver by name.
        Args:
            name (str): The name of the driver.
        Returns:
            LLMDriver: The driver instance.
        """
        pass

    @abstractmethod
    def list_supported_models(self) -> List[str]:
        """
        List all logical model names supported by this provider.
        Returns:
            List[str]: List of model names.
        """
        pass

    @abstractmethod
    def get_recommended_driver_for_model(self, model_name: str) -> LLMDriver:
        """
        Get the recommended driver for a given model name.
        Args:
            model_name (str): The logical model name.
        Returns:
            LLMDriver: The recommended driver instance for the model.
        """
        pass

    def create_agent(self, model_name: str = None, agent_name: str = None, **kwargs):
        """
        Factory method to create an LLMAgent using the recommended driver for a model.
        Args:
            model_name (str): The logical model name. If None, use the provider's default model.
            agent_name (str): Optional agent name.
            **kwargs: Additional parameters for the agent.
        Returns:
            LLMAgent: An instance of LLMAgent configured with the appropriate driver.
        """
        from janito.llm_agent import LLMAgent
        if model_name is None:
            model_name = self.get_model_name()
        driver = self.get_recommended_driver_for_model(model_name)
        return LLMAgent(driver, agent_name=agent_name, **kwargs)
