import http.client
from rich.console import Console
from janito.cli.config import config
from janito.cli.console import shared_console
from janito.cli.chat_mode.shell.commands.base import ShellCmdHandler


class TermwebLogTailShellHandler(ShellCmdHandler):
    help_text = "Show the last lines of the latest termweb logs"

    def run(self):
        lines = 20
        args = self.after_cmd_line.strip().split()
        if args and args[0].isdigit():
            lines = int(args[0])
        stdout_path = self.shell_state.termweb_stdout_path if self.shell_state else None
        stderr_path = self.shell_state.termweb_stderr_path if self.shell_state else None
        status = getattr(self.shell_state, "termweb_status", None)
        live_status = getattr(self.shell_state, "termweb_live_status", None)
        status_checked = getattr(self.shell_state, "termweb_live_checked_time", None)
        shared_console.print(
            f"[bold cyan][termweb] Current run status: {status} | Last health check: {live_status} at {status_checked}"
        )
        if not stdout_path and not stderr_path:
            shared_console.print(
                "[yellow][termweb] No termweb log files found for this session.[/yellow]"
            )
            return
        stdout_lines = stderr_lines = None
        if stdout_path:
            try:
                with open(stdout_path, encoding="utf-8") as f:
                    stdout_lines = f.readlines()[-lines:]
                if stdout_lines:
                    shared_console.print(
                        f"[yellow][termweb][stdout] Tail of {stdout_path}:\n"
                        + "".join(stdout_lines)
                    )
            except Exception:
                pass
        if stderr_path:
            try:
                with open(stderr_path, encoding="utf-8") as f:
                    stderr_lines = f.readlines()[-lines:]
                if stderr_lines:
                    shared_console.print(
                        f"[red][termweb][stderr] Tail of {stderr_path}:\n"
                        + "".join(stderr_lines)
                    )
            except Exception:
                pass
        if (not stdout_path or not stdout_lines) and (
            not stderr_path or not stderr_lines
        ):
            shared_console.print("[termweb] No output or errors captured in logs.")


def handle_termweb_status(*args, shell_state=None, **kwargs):
    if shell_state is None:
        console.print(
            "[red]No shell state available. Cannot determine termweb status.[/red]"
        )
        return
    from janito.cli.config import get_termweb_port

    port = get_termweb_port()
    port_source = "config"
    pid = getattr(shell_state, "termweb_pid", None)
    stdout_path = getattr(shell_state, "termweb_stdout_path", None)
    stderr_path = getattr(shell_state, "termweb_stderr_path", None)
    running = False
    if port and hasattr(shell_state, "termweb_live_status"):
        running = shell_state.termweb_live_status == "online"
    console.print("[bold cyan]TermWeb Server Status:[/bold cyan]")
    console.print(f"  Running: {'[green]Yes[/green]' if running else '[red]No[/red]'}")
    if pid:
        console.print(f"  PID: {pid}")
    if port:
        console.print(f"  Port: {port} (from {port_source})")
        url = f"http://localhost:{port}/"
        console.print(f"  URL: [underline blue]{url}[/underline blue]")
    else:
        console.print("  [yellow]No port configured in config.[/yellow]")
    if stdout_path:
        console.print(f"  Stdout log: {stdout_path}")
    if stderr_path:
        console.print(f"  Stderr log: {stderr_path}")


handle_termweb_status.help_text = (
    "Show status information about the running termweb server"
)
