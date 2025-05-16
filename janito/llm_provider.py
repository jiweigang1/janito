from abc import ABC, abstractmethod
from janito.llm_driver import LLMDriver

class LLMProvider(ABC):
    """
    Abstract base class for Large Language Model (LLM) providers.
    Each provider is intrinsically written for a single LLMDriver (model or capability).
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

    @property
    @abstractmethod
    def driver(self) -> LLMDriver:
        """
        Return the intrinsic driver instance for this provider.
        Returns:
            LLMDriver: The driver instance.
        """
        pass

    def create_agent(self, agent_name: str = None, **kwargs):
        """
        Factory method to create an Agent using the provider's intrinsic driver.
        Args:
            agent_name (str): Optional agent name.
            **kwargs: Additional parameters for the agent.
        Returns:
            Agent: An instance of Agent configured with the appropriate driver.
        """
        from janito.agent.agent import Agent
        return Agent(self.driver, agent_name=agent_name, **kwargs)
