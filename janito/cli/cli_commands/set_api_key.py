"""
CLI Command: Set API key for the current or selected provider
"""

from janito.provider_config import set_api_key
from janito.llm.auth import LLMAuthManager


def handle_set_api_key(args):
    api_key = getattr(args, "set_api_key", None)
    provider = getattr(args, "provider", None)
    if not provider:
        print("Error: --set-api-key requires -p/--provider to be specified.")
        return
    set_api_key(provider, api_key)
    auth_manager = LLMAuthManager()
    print(
        f"API key set for provider '{provider}'. Auth file updated: {auth_manager._auth_file}"
    )
