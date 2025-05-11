"""
ProviderRegistry: Handles provider listing and selection logic for janito CLI.
"""
from janito.llm_auth_manager import LLMAuthManager

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

    def select_provider(self, args):
        """Select provider based on CLI args and config."""
        from janito.provider_config import ProviderConfigManager
        provider_name = getattr(args, 'provider', None)
        if not provider_name:
            provider_name = ProviderConfigManager().get_default_provider()
        if not provider_name:
            from janito.providers.registry import LLMProviderRegistry
            auth_manager = LLMAuthManager()
            configured = []
            supported = LLMProviderRegistry.list_providers()
            for prov in supported:
                if auth_manager.get_credentials(prov):
                    configured.append(prov)
            self._print_provider_selection_error(configured, supported)
            return None
        return provider_name

    def _print_provider_selection_error(self, configured, supported):
        try:
            from rich import print as rich_print
            rich_print("[bold red]Error: No provider specified and no default provider is set.[/bold red]")
            if configured:
                rich_print("[yellow]Providers with authentication configured:[/yellow]")
                for prov in configured:
                    rich_print(f"- [green]{prov}[/green]")
                rich_print("Use [cyan]prompt --provider PROVIDER[/cyan] to select one, or set a default with [cyan]--set-provider PROVIDER[/cyan].")
            else:
                rich_print("[yellow]No providers have authentication configured.[/yellow]")
                if supported:
                    rich_print("Supported providers:")
                    for prov in supported:
                        rich_print(f"- [cyan]{prov}[/cyan]")
                    rich_print("Set authentication for a provider using [cyan]set-api-key PROVIDER API_KEY[/cyan].")
                else:
                    rich_print("[red]No providers are registered in this installation.[/red]")
        except ImportError:
            print("Error: No provider specified and no default provider is set.")
            if configured:
                print("Providers with authentication configured:")
                for prov in configured:
                    print(f"- {prov}")
                print("Use prompt --provider PROVIDER to select one, or set a default with --set-provider PROVIDER.")
            else:
                print("No providers have authentication configured.")
                if supported:
                    print("Supported providers:")
                    for prov in supported:
                        print(f"- {prov}")
                    print("Set authentication for a provider using set-api-key PROVIDER API_KEY.")
                else:
                    print("No providers are registered in this installation.")

# For backward compatibility
def list_providers():
    """Legacy function for listing providers, now uses ProviderRegistry class."""
    ProviderRegistry().list_providers()

def select_provider(args):
    """Legacy function for selecting provider, now uses ProviderRegistry class."""
    return ProviderRegistry().select_provider(args)
