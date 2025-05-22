"""Handles LLM driver config preparation and execution modes."""
from janito.llm.driver_config import LLMDriverConfig
from janito.provider_config import get_default_provider
from janito.cli.verbose_output import print_verbose_info


def prepare_llm_driver_config(args, modifiers):
    provider = getattr(args, 'provider', None)
    if provider is None:
        provider = get_default_provider()
        if provider and getattr(args, 'verbose', False):
            print_verbose_info("Default provider", provider, style="magenta", align_content=True)
        elif provider is None:
            print("Error: No provider selected and no default_provider found in config. Please set a provider using '-p PROVIDER', '--set default_provider=provider_name', or configure a default provider.")
            return None, None, None
    model = getattr(args, 'model', None)
    driver_config_data = {"model": model}
    for field in LLMDriverConfig.__dataclass_fields__:
        if field in modifiers and field != "model":
            driver_config_data[field] = modifiers[field]
    llm_driver_config = LLMDriverConfig(**driver_config_data)
    agent_role = modifiers.get("role", "software developer")
    return provider, llm_driver_config, agent_role


def handle_runner(args, provider, llm_driver_config, agent_role):
    from janito.provider_registry import ProviderRegistry
    provider_instance = ProviderRegistry().get_instance(provider, llm_driver_config)
    mode = get_prompt_mode(args)
    if getattr(args, 'verbose', False):
        print_verbose_info("Active LLMDriverConfig (after provider)", llm_driver_config, style="green")
        print_verbose_info("Agent role", agent_role, style="green")
    if mode == "single_shot":
        from janito.cli.single_shot_mode.handler import PromptHandler as SingleShotPromptHandler
        handler = SingleShotPromptHandler(args, provider_instance, llm_driver_config, role=agent_role)
        handler.handle()
    else:
        from janito.cli.chat_mode.session import ChatSession
        from rich.console import Console
        console = Console()
        session = ChatSession(console, provider_instance, llm_driver_config, role=agent_role)
        session.run()

def get_prompt_mode(args):
    return 'single_shot' if getattr(args, 'user_prompt', None) else 'chat_mode'
