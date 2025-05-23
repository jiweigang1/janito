"""
ProviderRegistry: Handles provider listing and selection logic for janito CLI.
"""
from rich.table import Table
from janito.cli.console import shared_console
from janito.providers.registry import LLMProviderRegistry
from janito.llm.auth import LLMAuthManager
import sys
from janito.exceptions import MissingProviderSelectionException

class ProviderRegistry:
    def list_providers(self):
        """List all supported LLM providers as a table using rich, showing if auth is configured and supported model names."""
        from rich.table import Table
        from rich.console import Console
        from janito.providers.registry import LLMProviderRegistry
        from janito.llm.auth import LLMAuthManager
        providers = LLMProviderRegistry.list_providers()
        auth_manager = LLMAuthManager()
        console = shared_console

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
        table.add_column("Maintainer", style="yellow", justify="center")
        table.add_column("Auth", style="green", justify="center")
        table.add_column("Model Names", style="magenta")
        # Gather data and sort by auth configured
        rows = []
        for p in providers:
            creds = auth_manager.get_credentials(p)
            configured = "✅ Auth" if creds else ""
            model_names = "-"
            maintainer = ""
            try:
                provider_class = LLMProviderRegistry.get(p)
                _maintainer_val = getattr(provider_class, "maintainer", "-")
                if _maintainer_val == "Needs maintainer":
                    # Show in red with emoji 🚨
                    maintainer = "[red]🚨 Needs maintainer[/red]"
                else:
                    maintainer = f"👤 {_maintainer_val}"
            except Exception:
                maintainer = "-"
            try:
                if p in provider_to_specs:
                    mod = __import__(provider_to_specs[p], fromlist=["MODEL_SPECS"])
                    model_names = ", ".join(mod.MODEL_SPECS.keys())
            except Exception as e:
                model_names = "(Error)"
            rows.append((p, maintainer, configured, model_names))
        # Sort: 1) Maintained first, 2) Auth next
        def maintainer_sort_key(row):
            maint = row[1]
            is_needs_maint = "Needs maintainer" in maint
            return (is_needs_maint, row[2] != "✅ Auth")
        rows.sort(key=maintainer_sort_key)

        for idx, (p, maintainer, configured, model_names) in enumerate(rows):
            table.add_row(p, maintainer, configured, model_names)
            if idx != len(rows) - 1:
                table.add_section()
        console.print(table)

    def get_provider(self, provider_name):
        """Return the provider class for the given provider name."""
        from janito.providers.registry import LLMProviderRegistry
        if not provider_name:
            raise ValueError("Provider name must be specified.")
        return LLMProviderRegistry.get(provider_name)

    def get_instance(self, provider_name, config=None):
        """Return an instance of the provider for the given provider name, optionally passing a config object."""
        provider_class = self.get_provider(provider_name)
        if provider_class is None:
            raise ValueError(f"No provider class found for '{provider_name}'")
        if config is not None:
            return provider_class(config=config)
        return provider_class()

# For backward compatibility
def list_providers():
    """Legacy function for listing providers, now uses ProviderRegistry class."""
    ProviderRegistry().list_providers()
