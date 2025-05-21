import importlib
import sys
from janito.cli.config import config

# Helper for model validation by provider
PROVIDER_TO_MODEL_MODULE = {
    'openai': 'janito.providers.openai.model_info',
    'azure_openai': 'janito.providers.azure_openai.model_info',
    'google': 'janito.providers.google.model_info',
    'mistralai': 'janito.providers.mistralai.model_info',
    'dashscope': 'janito.providers.dashscope.model_info',
}

def validate_modifiers(modifiers, config_mgr=None):
    config_mgr = config_mgr or config
    provider = modifiers.get('provider') or config_mgr.get('provider')
    if not provider:
        print("Error: No provider specified (use --provider or set a default with --set-provider).", file=sys.stderr)
        sys.exit(1)
    model = modifiers.get('model')
    if model:
        module_name = PROVIDER_TO_MODEL_MODULE.get(provider)
        if not module_name:
            print(f"Error: Unknown provider '{provider}'.", file=sys.stderr)
            sys.exit(1)
        try:
            model_module = importlib.import_module(module_name)
            model_specs = getattr(model_module, 'MODEL_SPECS', {})
        except ImportError as e:
            print(f"Error: Unable to load models for provider '{provider}'. {e}", file=sys.stderr)
            sys.exit(1)
        if model not in model_specs:
            print(f"Error: Model '{model}' not found for provider '{provider}'. Valid models: {list(model_specs.keys())}", file=sys.stderr)
            sys.exit(1)
    return provider, model
