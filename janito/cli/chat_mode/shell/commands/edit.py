import os
import webbrowser
from janito.cli.console import shared_console
from janito.cli.chat_mode.shell.commands.base import ShellCmdHandler


class EditShellHandler(ShellCmdHandler):
    help_text = "Open a file in the browser-based editor"

    def run(self):
        filename = self.after_cmd_line.strip()
        if not filename:
            shared_console.print("[red]Usage: /edit <filename>[/red]")
            return
        if not os.path.isfile(filename):
            shared_console.print(f"[red]File not found:[/red] {filename}")
            return
        from janito.cli.config import get_termweb_port

        port = get_termweb_port()
        url = f"http://localhost:{port}/?path={filename}"
        shared_console.print(
            f"[green]Opening in browser:[/green] [underline blue]{url}[/underline blue]"
        )
        webbrowser.open(url)
