from abc import ABC, abstractmethod
import importlib
from janito.llm_driver import LLMDriver

class LLMProvider(ABC):
    """
    Abstract base class for Large Language Model (LLM) providers.

    Subclasses must implement the core interface for interacting with LLM APIs and define `provider_name` as a class attribute.
    """

    name: str = None  # Must be set on subclasses

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, 'name') or not isinstance(getattr(cls, 'name'), str) or not cls.name:
            raise TypeError(f"Class {cls.__name__} must define a class attribute 'name' (non-empty str)")


    @property
    @abstractmethod
    def driver(self) -> LLMDriver:
        pass

    def get_model_info(self, model_name=None):
        """
        Return the info dict for a given model (driver, params, etc). If model_name is None, return all model info dicts.
        MODEL_SPECS must be dict[str, ModelInfo].
        """
        if not hasattr(self, 'MODEL_SPECS'):
            raise NotImplementedError("This provider does not have a MODEL_SPECS attribute.")
        if model_name is None:
            return {name: model_info.to_dict() for name, model_info in self.MODEL_SPECS.items()}
        if model_name in self.MODEL_SPECS:
            return self.MODEL_SPECS[model_name].to_dict()
        return None

    def get_driver_for_model(self, config: dict = None):
        self._validate_model_specs()
        model_name = self._get_model_name_from_config(config)
        spec = self._get_model_spec_entry(model_name)
        driver_name = self._get_driver_name_from_spec(spec)
        driver_class = self._resolve_driver_class(driver_name)
        self._validate_required_config(driver_class, config, driver_name)
        return driver_class(
            type(self).name,
            model_name,
            getattr(self, '_api_key', None),
            getattr(self, '_tool_registry', None),
            config or {}
        )

    def _validate_model_specs(self):
        if not hasattr(self, 'MODEL_SPECS'):
            raise NotImplementedError("This provider does not have a MODEL_SPECS attribute.")

    def _get_model_name_from_config(self, config):
        return (config or {}).get('model_name', getattr(self, 'DEFAULT_MODEL', None))

    def _get_model_spec_entry(self, model_name):
        spec = self.MODEL_SPECS.get(model_name, None)
        if spec is None:
            raise ValueError(f"Model '{model_name}' not found in MODEL_SPECS.")
        return spec

    def _get_driver_name_from_spec(self, spec):
        driver_name = None
        if hasattr(spec, 'other') and isinstance(spec.other, dict):
            driver_name = spec.other.get('driver', None)
        if not driver_name and hasattr(spec, 'driver'):
            driver_name = spec.driver
        return driver_name

    def _resolve_driver_class(self, driver_name):
        if not driver_name:
            raise NotImplementedError("No driver class found or specified for this MODEL_SPECS entry.")
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
            return getattr(mod, driver_name)
        raise NotImplementedError("No driver class found for driver_name: {}".format(driver_name))

    def _validate_required_config(self, driver_class, config, driver_name):
        required = getattr(driver_class, 'required_config', None)
        if required:
            missing = [k for k in required if not config or k not in config or config.get(k) in (None, "")]
            if missing:
                raise ValueError(f"Missing required config for {driver_name}: {', '.join(missing)}")

    def create_agent(self, agent_name: str = None, **kwargs):
        from janito.agent.agent import Agent
        return Agent(self.driver, agent_name=agent_name, **kwargs)
