from abc import ABC, abstractmethod
import importlib
from janito.llm_driver import LLMDriver

class LLMProvider(ABC):
    """
    Abstract base class for Large Language Model (LLM) providers.
    Each provider is intrinsically written for a single LLMDriver (model or capability).
    Subclasses should implement the core interface for interacting with LLM APIs.
    """

    @abstractmethod
    def get_model_name(self) -> str:
        pass

    @property
    @abstractmethod
    def driver(self) -> LLMDriver:
        pass

    @classmethod
    def list_models(cls):
        if hasattr(cls, 'MODEL_SPECS'):
            return [dict(name=name, **spec) for name, spec in cls.MODEL_SPECS.items()]
        raise NotImplementedError("This provider does not have a MODEL_SPECS attribute.")

    def get_driver_for_model(self, model_name: str):
        if not hasattr(self, 'MODEL_SPECS'):
            raise NotImplementedError("This provider does not have a MODEL_SPECS attribute.")
        spec = self.MODEL_SPECS.get(model_name, {})
        # Default: look for 'driver', fall back to 'LLMDriver'
        driver_name = spec.get('driver', None)
        driver_class = None
        # Simple convention: try to import from usual locations, override in subclass if needed
        if driver_name:
            # Compose module path based on class naming convention, e.g. for 'OpenAIModelDriver'
            module_root = 'janito.drivers'
            probable_path = None
            if 'OpenAIResponsesModelDriver' == driver_name:
                probable_path = f'openai_responses.driver'
            elif 'OpenAIModelDriver' == driver_name:
                probable_path = f'openai.driver'
            # Can extend with elifs for other providers here
            if probable_path is not None:
                module_path = f"{module_root}.{probable_path}"
                mod = importlib.import_module(module_path)
                driver_class = getattr(mod, driver_name)
        if driver_class is None:
            # Fallback to a generic class: subclasses must override
            raise NotImplementedError("No driver class found or specified for this MODEL_SPECS entry.")
        return driver_class(
            getattr(self, 'PROVIDER_NAME', ''),
            model_name,
            getattr(self, '_api_key', None),
            getattr(self, '_tool_registry', None)
        )

    def create_agent(self, agent_name: str = None, **kwargs):
        from janito.agent.agent import Agent
        return Agent(self.driver, agent_name=agent_name, **kwargs)
