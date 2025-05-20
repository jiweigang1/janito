"""
Provider and agent setup logic for janito CLI (shared).
"""
from janito.provider_registry import ProviderRegistry
from janito.cli.config import config
import os
from janito.platform_discovery import PlatformDiscovery
from janito.cli.config import config
from pathlib import Path
from janito.tool_registry import ToolRegistry

def setup_provider():
    provider_registry = ProviderRegistry()
    provider_name = config.get('provider')

    if not provider_name:
        error_message = (
            "Error: No provider specified and no default provider is set.\n"
            "Providers with authentication configured:\n"
            "(no configured providers found)\n"            "Use prompt --provider PROVIDER to select one, or set a default with --set-provider PROVIDER."
        )
        raise RuntimeError(error_message)

    provider_cls = provider_registry.get_provider(provider_name)
    # Pass config dict (with model_name if present) to the provider,
    # not directly to a driver instance.
    model_name = config.get('model')
    config_dict = {'model_name': model_name} if model_name else {}
    provider_instance = provider_cls(config=config_dict)
    return provider_instance

def setup_agent(provider_instance, conversation_history, template_path=None, **kwargs):
    system_prompt = config.get('system_prompt')
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
    provider_instance = setup_provider()
    if not provider_instance:
        return None
    tool_registry = ToolRegistry()
    all_tool_classes = tool_registry.get_tool_classes()
    templates_dir = Path(__file__).parent.parent / 'agent' / 'templates' / 'profiles'
    main_template_path = str(templates_dir / 'system_prompt_template_main.txt.j2')
    agent = provider_instance.create_agent(
        system_prompt=config.get('system_prompt'),
        history=conversation_history,
        tools=all_tool_classes,
        template_path=main_template_path
    )
    return agent
