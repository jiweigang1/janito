from rich.console import Console
from rich.pretty import Pretty

from janito.config import config
from janito.cli.config import CONFIG_OPTIONS


def resolve_effective_model(provider_name):
    # Try provider-specific model, then global model, then provider default
    provider_cfg = config.get_provider_config(provider_name)
    model = provider_cfg.get("model") if provider_cfg else None
    if not model:
        model = config.get("model")
    if not model:
        try:
            from janito.provider_registry import ProviderRegistry

            provider_class = ProviderRegistry().get_provider(provider_name)
            model = getattr(provider_class, "DEFAULT_MODEL", None)
        except Exception:
            model = None
    return model


def handle_show_config(args):
    console = Console()
    provider = config.get("provider")
    model = config.get("model")
    # Show all providers with their effective model
    from janito.provider_registry import ProviderRegistry

    provider_names = []
    try:
        provider_names = ProviderRegistry()._get_provider_names()
    except Exception:
        pass
    console.print("[bold green]Current configuration:[/bold green]")
    console.print(f"[bold yellow]Current provider:[/bold yellow] {provider!r}\n")
    if model is not None:
        console.print(f"[bold yellow]Global model:[/bold yellow] {model!r}\n")
    if provider_names:
        console.print("[bold cyan]Provider specific default models:[/bold cyan]")
        for pname in provider_names:
            eff_model = resolve_effective_model(pname)
            prov_cfg = config.get_provider_config(pname)
            prov_model = prov_cfg.get("model") if prov_cfg else None
            extra = f" (override)" if prov_model else ""
            sel = "[default]" if pname == provider else ""
            console.print(
                f"  [bold]{pname}[/bold]{' '+sel if sel else ''}: model = [magenta]{eff_model}[/magenta]{extra}"
            )
