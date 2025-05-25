from janito.llm.agent import LLMAgent
from janito.drivers.driver_registry import get_driver_class

def create_llm_agent_from_provider(provider, model_name=None, tools_adapter=None, agent_name=None, **kwargs):
    '''
    Factory for constructing agents from providers using model info (driver string) pattern.
    '''
    # 1. Get model info from provider
    model_info = provider.get_model_info(model_name or provider.DEFAULT_MODEL)
    driver_name = model_info['driver'] if isinstance(model_info, dict) else getattr(model_info, 'driver', None)
    if not driver_name:
        raise ValueError("No driver available for requested model.")
    driver_cls = get_driver_class(driver_name)
    # 2. Get config from provider (assume provider._info or similar)
    config = getattr(provider, '_info', None)
    if config is None:
        # If provider structure differs, you can add more discovery
        raise ValueError("Provider does not have a valid config object (_info). Update factory accordingly.")
    driver = driver_cls(config, tools_adapter)
    return LLMAgent(driver, tools_adapter, agent_name=agent_name or getattr(provider, 'name', None), **kwargs)
