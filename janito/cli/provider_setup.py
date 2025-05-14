"""
Provider and agent setup logic for janito CLI (shared).
"""
from janito.provider_registry import ProviderRegistry
from janito.provider_config import ProviderConfigManager
import os
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from janito.platform_discovery import PlatformDiscovery

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
    system_prompt = getattr(args, 'system', None)
    if system_prompt and os.path.isfile(system_prompt):
        if system_prompt.endswith('.j2'):
            # Render Jinja2 template with auto-generated variables
            template_path = Path(system_prompt)
            env = Environment(
                loader=FileSystemLoader(str(template_path.parent)),
                autoescape=select_autoescape(["txt", "j2"]),
            )
            template = env.get_template(template_path.name)
            pd = PlatformDiscovery()
            vars = {
                "role": "software developer",
                "platform": pd.get_platform_name(),
                "python_version": pd.get_python_version(),
                "shell_info": pd.detect_shell(),
            }
            system_prompt = template.render(**vars)
        else:
            with open(system_prompt, 'r', encoding='utf-8') as f:
                system_prompt = f.read()
    return provider_cls().create_agent(
        system_prompt=system_prompt,
        thinking_budget=thinking_budget
    )
