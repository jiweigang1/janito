"""
CLI Command: Set a provider configuration key-value
"""
from janito.cli.provider_setup import setup_provider

_provider_instance = None

def get_provider_instance():
    global _provider_instance
    if _provider_instance is None:
        _provider_instance = setup_provider()
    return _provider_instance

def handle_set_provider_kv(args, mgr):
    set_arg = args.set.strip()
    if '=' not in set_arg:
        print("Error: --set requires argument in the form [PROVIDER_NAME[.MODEL].]KEY=VALUE")
        print("Example: --set openai.gpt-3.5-turbo.max_tokens=4096 or --set openai.base_url=https://api... or --set model=gpt-3")
        return
    keypart, value = set_arg.split('=', 1)
    dot_parts = keypart.split('.')
    if len(dot_parts) == 3:
        provider, model, key = dot_parts
    elif len(dot_parts) == 2:
        provider, key = dot_parts
        model = None
    else:
        provider_instance = get_provider_instance()
        provider = getattr(provider_instance, 'name', None)
        if not provider:
            print("Error: No provider could be determined from setup_provider.")
            return
        model = None
        key = keypart
    if not provider:
        print("Error: No provider could be determined from setup_provider.")
        return
    if model:
        mgr.set_provider_model_config(provider, model, key, value)
        print(f"Set config for provider '{provider}', model '{model}': {key} = {value}")
    else:
        mgr.set_provider_config(provider, key, value)
        print(f"Set config for provider '{provider}': {key} = {value}")
