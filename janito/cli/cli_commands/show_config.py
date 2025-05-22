from rich.console import Console
from rich.pretty import Pretty

from janito.config import config

def handle_show_config(args):
    console = Console()
    cfg = config.all()
    console.print("[bold green]Current configuration:[/bold green]")
    console.print(Pretty(cfg, expand_all=True))
