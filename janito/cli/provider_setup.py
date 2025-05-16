"""
Provider and agent setup logic for janito CLI (shared).
"""
from janito.provider_registry import ProviderRegistry
from janito.provider_config import ProviderConfigManager
import os
from janito.platform_discovery import PlatformDiscovery
from janito.cli.runtime_config import runtime_config

def setup_provider(args, return_class=False):
    provider_registry = ProviderRegistry()
    provider_config_mgr = ProviderConfigManager()
    provider_name = provider_registry.select_provider(args)
    if not provider_name:
        return None if not return_class else (None, None)
    from janito.providers.registry import LLMProviderRegistry
    provider_cls = LLMProviderRegistry.get(provider_name)
    if return_class:
        return provider_cls, None
    return provider_name

def setup_agent(provider_cls, runtime_config, conversation_history, template_path=None, **kwargs):
    system_prompt = getattr(runtime_config, 'system_prompt', None)
    model_name = getattr(runtime_config, 'model', None)
    provider_instance = provider_cls(model_name=model_name)
    agent = provider_instance.create_agent(
        system_prompt=system_prompt,
        history=conversation_history,
        **kwargs
    )
    if not system_prompt and template_path:
        agent.set_system_using_template(template_path)
    return agent

