"""
Provider and agent setup logic for janito CLI (shared).
"""
from janito.provider_registry import ProviderRegistry
from janito.provider_config import ProviderConfigManager
import os
from janito.platform_discovery import PlatformDiscovery
from janito.cli.runtime_config import runtime_config
from pathlib import Path
from janito.tool_registry import ToolRegistry

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
    system_prompt = runtime_config.get('system_prompt')
    model_name = runtime_config.get('model')

    provider_instance = provider_cls(model_name=model_name)
    agent = provider_instance.create_agent(
        system_prompt=system_prompt,
        history=conversation_history,
        **kwargs
    )
    if not system_prompt and template_path:
        agent.set_system_using_template(template_path)
    return agent

def setup_main_agent(args, conversation_history):
    """
    Instantiate and return a main agent for either chat or one-shot mode.
    Skips shell state components.
    """
    provider_cls = setup_provider(args, return_class=True)[0]
    if not provider_cls:
        return None
    tool_registry = ToolRegistry()
    all_tool_classes = tool_registry.get_tool_classes()
    templates_dir = Path(__file__).parent.parent / 'agent' / 'templates' / 'profiles'
    main_template_path = str(templates_dir / 'system_prompt_template_main.txt.j2')
    agent = setup_agent(
        provider_cls,
        runtime_config,
        conversation_history=conversation_history,
        tools=all_tool_classes,
        template_path=main_template_path
    )
    return agent
