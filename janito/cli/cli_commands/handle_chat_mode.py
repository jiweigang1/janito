"""
Chat mode handler for janito CLI
"""
from janito.cli.config import config

def handle_chat_mode(args, parser):
    # Apply relevant CLI args as runtime config overrides
    cli_overrides = {key: getattr(args, key) for key in ['provider', 'model', 'role', 'temperature', 'system'] if getattr(args, key, None) is not None}
    if 'system' in cli_overrides:
        cli_overrides['system_prompt'] = cli_overrides.pop('system')
    if cli_overrides:
        config.apply_runtime_overrides(cli_overrides)
    termweb_proc = None
    try:
        if not getattr(args, 'no_termweb', False):
            from janito.cli.termweb_starter import start_termweb
            from janito.cli.config import set_termweb_port, get_termweb_port
            set_termweb_port(getattr(args, 'termweb_port', get_termweb_port()))
            try:
                from janito.cli.provider_setup import setup_provider
                provider_instance = setup_provider()
            except RuntimeError as e:
                from rich.console import Console
                Console().print(f'[red][bold]Error:[/bold] {e}[/red]')
                return
            termweb_proc, started, termweb_stdout_path, termweb_stderr_path = start_termweb(get_termweb_port())
        from janito.cli.chat_mode.chat_entry import main as chat_mode_main
        chat_mode_main()
    finally:
        if termweb_proc:
            termweb_proc.terminate()
            termweb_proc.wait()
