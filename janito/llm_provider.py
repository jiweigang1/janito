from abc import ABC, abstractmethod
import importlib
from janito.llm_driver import LLMDriver

class LLMProvider(ABC):
    """
    Abstract base class for Large Language Model (LLM) providers.

    Subclasses must implement the core interface for interacting with LLM APIs and define `provider_name` as a class attribute.
    """

    provider_name: str = None  # Must be set on subclasses

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, 'provider_name') or not isinstance(getattr(cls, 'provider_name'), str) or not cls.provider_name:
            raise TypeError(f"Class {cls.__name__} must define a class attribute 'provider_name' (non-empty str)")

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

    def get_driver_for_model(self, model_name: str, config: dict = None):
        if not hasattr(self, 'MODEL_SPECS'):
            raise NotImplementedError("This provider does not have a MODEL_SPECS attribute.")
        spec = self.MODEL_SPECS.get(model_name, {})
        driver_name = spec.get('driver', None)
        driver_class = None
        if driver_name:
            module_root = 'janito.drivers'
            probable_path = None
            if 'OpenAIResponsesModelDriver' == driver_name:
                probable_path = f'openai_responses.driver'
            elif 'OpenAIModelDriver' == driver_name:
                probable_path = f'openai.driver'
            elif 'AzureOpenAIModelDriver' == driver_name:
                probable_path = f'azure_openai.driver'
            if probable_path is not None:
                module_path = f"{module_root}.{probable_path}"
                mod = importlib.import_module(module_path)
                driver_class = getattr(mod, driver_name)
        if driver_class is None:
            raise NotImplementedError("No driver class found or specified for this MODEL_SPECS entry.")
        # Validate required config fields if specified by the driver
        required = getattr(driver_class, 'required_config', None)
        if required:
            missing = [k for k in required if not config or k not in config or config.get(k) in (None, "")]
            if missing:
                raise ValueError(f"Missing required config for {driver_name}: {', '.join(missing)}")
        return driver_class(
            type(self).provider_name,
            model_name,
            getattr(self, '_api_key', None),
            getattr(self, '_tool_registry', None),
            config or {}
        )

    def create_agent(self, agent_name: str = None, **kwargs):
        from janito.agent.agent import Agent
        return Agent(self.driver, agent_name=agent_name, **kwargs)
