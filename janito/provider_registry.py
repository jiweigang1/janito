"""
ProviderRegistry: Handles provider listing and selection logic for janito CLI.
"""
from janito.llm.auth import LLMAuthManager
import sys
from janito.exceptions import MissingProviderSelectionException

class ProviderRegistry:
    def list_providers(self):
        """List all supported LLM providers as a table using rich, showing if auth is configured and supported model names."""
        try:
            from rich.table import Table
            from rich.console import Console
            from janito.providers.registry import LLMProviderRegistry
            from janito.llm.auth import LLMAuthManager
            providers = LLMProviderRegistry.list_providers()
            auth_manager = LLMAuthManager()
            console = Console()

            # Model specs files to import
            provider_to_specs = {
                'openai': 'janito.providers.openai.model_info',
                'azure_openai': 'janito.providers.azure_openai.model_info',
                'google': 'janito.providers.google.model_info',
                'mistralai': 'janito.providers.mistralai.model_info',
                'dashscope': 'janito.providers.dashscope.model_info',
            }

            table = Table(title="Supported LLM Providers")
            table.add_column("Provider", style="cyan")
            table.add_column("Auth", style="green", justify="center")
            table.add_column("Model Names", style="magenta")
            # Gather data and sort by auth configured
            rows = []
            for p in providers:
                creds = auth_manager.get_credentials(p)
                configured = "✅" if creds else ""
                model_names = "-"
                try:
                    if p in provider_to_specs:
                        mod = __import__(provider_to_specs[p], fromlist=["MODEL_SPECS"])
                        model_names = ", ".join(mod.MODEL_SPECS.keys())
                except Exception as e:
                    model_names = "(Error)"
                rows.append((p, configured, model_names))
            # Sort with configured (check) first
            rows.sort(key=lambda r: r[1] != "✅")
            for idx, (p, configured, model_names) in enumerate(rows):
                table.add_row(p, configured, model_names)
                if idx != len(rows) - 1:
                    table.add_section()
            console.print(table)
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
