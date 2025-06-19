"""
ProviderRegistry: Handles provider listing and selection logic for janito CLI.
"""

from rich.table import Table
from janito.cli.console import shared_console
from janito.providers.registry import LLMProviderRegistry
from janito.providers.provider_static_info import STATIC_PROVIDER_METADATA
from janito.llm.auth import LLMAuthManager
import sys
from janito.exceptions import MissingProviderSelectionException


class ProviderRegistry:
    def list_providers(self):
        """List all supported LLM providers as a table using rich, showing if auth is configured and supported model names."""
        providers = self._get_provider_names()
        table = self._create_table()
        rows = self._get_all_provider_rows(providers)
        self._add_rows_to_table(table, rows)
        self._print_table(table)

    def _get_provider_names(self):
        return list(STATIC_PROVIDER_METADATA.keys())

    def _create_table(self):
        table = Table(title="Supported LLM Providers")
        table.add_column("Provider", style="cyan")
        table.add_column("Maintainer", style="yellow", justify="center")
        table.add_column("Model Names", style="magenta")
        return table

    def _get_all_provider_rows(self, providers):
        rows = []
        for p in providers:
            info = self._get_provider_info(p)
            # info is (provider_name, maintainer, model_names, skip)
            if len(info) == 4 and info[3]:
                continue  # skip providers flagged as not implemented
            rows.append(info[:3])
        rows.sort(key=self._maintainer_sort_key)
        return rows

    def _add_rows_to_table(self, table, rows):
        for idx, (p, maintainer, model_names) in enumerate(rows):
            table.add_row(p, maintainer, model_names)
            if idx != len(rows) - 1:
                table.add_section()

    def _print_table(self, table):
        shared_console.print(table)

    def _get_provider_info(self, provider_name):
        static_info = STATIC_PROVIDER_METADATA.get(provider_name, {})
        maintainer_val = static_info.get("maintainer", "-")
        maintainer = (
            "[red]🚨 Needs maintainer[/red]"
            if maintainer_val == "Needs maintainer"
            else f"👤 {maintainer_val}"
        )
        model_names = "-"
        unavailable_reason = None
        skip = False
        try:
            provider_class = LLMProviderRegistry.get(provider_name)
            creds = LLMAuthManager().get_credentials(provider_name)
            provider_instance = None
            instantiation_failed = False
            try:
                provider_instance = provider_class()
            except NotImplementedError:
                skip = True
                unavailable_reason = "Not implemented"
                model_names = f"[red]❌ Not implemented[/red]"
            except Exception as e:
                instantiation_failed = True
                unavailable_reason = (
                    f"Unavailable (import error or missing dependency): {str(e)}"
                )
                model_names = f"[red]❌ {unavailable_reason}[/red]"
            if not instantiation_failed and provider_instance is not None:
                available, unavailable_reason = self._get_availability(
                    provider_instance
                )
                if (
                    not available
                    and unavailable_reason
                    and "not implemented" in str(unavailable_reason).lower()
                ):
                    skip = True
                if available:
                    model_names = self._get_model_names(provider_name)
                else:
                    model_names = f"[red]❌ {unavailable_reason}[/red]"
        except Exception as import_error:
            model_names = f"[red]❌ Unavailable (cannot import provider module): {str(import_error)}[/red]"
        return (provider_name, maintainer, model_names, skip)

    def _get_availability(self, provider_instance):
        try:
            available = getattr(provider_instance, "available", True)
            unavailable_reason = getattr(provider_instance, "unavailable_reason", None)
        except Exception as e:
            available = False
            unavailable_reason = f"Error reading runtime availability: {str(e)}"
        return available, unavailable_reason

    def _get_model_names(self, provider_name):
        provider_to_specs = {
            "openai": "janito.providers.openai.model_info",
            "azure_openai": "janito.providers.azure_openai.model_info",
            "google": "janito.providers.google.model_info",
            "mistralai": "janito.providers.mistralai.model_info",
            "deepseek": "janito.providers.deepseek.model_info",
        }
        if provider_name in provider_to_specs:
            try:
                mod = __import__(
                    provider_to_specs[provider_name], fromlist=["MODEL_SPECS"]
                )
                return ", ".join(mod.MODEL_SPECS.keys())
            except Exception:
                return "(Error)"
        return "-"

    def _maintainer_sort_key(self, row):
        maint = row[1]
        is_needs_maint = "Needs maintainer" in maint
        return (is_needs_maint, row[2] != "✅ Auth")

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
