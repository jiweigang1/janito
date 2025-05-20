from rich.console import Console
from rich.pretty import Pretty

def handle_show_config(config_mgr):
    console = Console()
    cfg = config_mgr.all()
    console.print("[bold green]Current configuration:[/bold green]")
    console.print(Pretty(cfg, expand_all=True))
