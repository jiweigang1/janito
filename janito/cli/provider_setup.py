"""
Provider and agent setup logic for janito CLI (shared).
"""
from janito.provider_registry import ProviderRegistry
from janito.provider_config import ProviderConfigManager

def setup_provider(args, return_class=False):
    provider_registry = ProviderRegistry()
    provider_config_mgr = ProviderConfigManager()
    provider_name = provider_registry.select_provider(args)
    if not provider_name:
        return None if not return_class else (None, None)
    from janito.providers.registry import LLMProviderRegistry
    provider_cls = LLMProviderRegistry.get(provider_name)
    thinking_budget = getattr(args, 'thinking_budget', None)
    if thinking_budget is None:
        thinking_budget = provider_config_mgr.get_thinking_budget(provider_name)
    else:
        thinking_budget = int(thinking_budget)
    if return_class:
        return provider_cls, thinking_budget
    return provider_name

def setup_agent(provider_cls, args, thinking_budget):
    return provider_cls().create_agent(
        system_prompt=getattr(args, 'system', None),
        thinking_budget=thinking_budget
    )
