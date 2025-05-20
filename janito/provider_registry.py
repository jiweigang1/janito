"""
ProviderRegistry: Handles provider listing and selection logic for janito CLI.
"""
from janito.llm_auth_manager import LLMAuthManager
import sys
from janito.exceptions import MissingProviderSelectionException

class ProviderRegistry:
    def list_providers(self):
        """List all supported LLM providers."""
        try:
            from janito.providers.registry import LLMProviderRegistry
            providers = LLMProviderRegistry.list_providers()
            if providers:
                print("Supported providers:")
                for p in providers:
                    print(f"- {p}")
            else:
                print("No providers are currently registered.")
        except ImportError:
            print("Provider registry not available.")

    def get_provider(self, provider_name):
        """Return the provider class for the given provider name."""
        from janito.providers.registry import LLMProviderRegistry
        if not provider_name:
            raise ValueError("Provider name must be specified.")
        return LLMProviderRegistry.get(provider_name)

# For backward compatibility
def list_providers():
    """Legacy function for listing providers, now uses ProviderRegistry class."""
    ProviderRegistry().list_providers()
