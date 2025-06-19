from janito.cli.console import shared_console
from janito.cli.chat_mode.shell.commands.base import ShellCmdHandler


class LivelogsShellHandler(ShellCmdHandler):
    help_text = "Show the last lines of livereload logs. Usage: /livelogs [lines]"

    def run(self):
        lines_arg = self.after_cmd_line.strip()
        lines = 20
        if lines_arg and lines_arg.isdigit():
            lines = int(lines_arg)
        stdout_path = self.shell_state.termweb_stdout_path if self.shell_state else None
        stderr_path = (
            self.shell_state.livereload_stderr_path if self.shell_state else None
        )
        if not stdout_path and not stderr_path:
            shared_console.print(
                "[yellow][livereload] No livereload log files found for this session.[/yellow]"
            )
            return
        stdout_lines = []
        stderr_lines = []
        if stdout_path:
            try:
                with open(stdout_path, encoding="utf-8") as f:
                    stdout_lines = f.readlines()[-lines:]
                if stdout_lines:
                    shared_console.print(
                        f"[yellow][livereload][stdout] Tail of {stdout_path}:\n"
                        + "".join(stdout_lines)
                    )
            except Exception as e:
                shared_console.print(f"[red][livereload][stdout] Error: {e}[/red]")
        if stderr_path:
            try:
                with open(stderr_path, encoding="utf-8") as f:
                    stderr_lines = f.readlines()[-lines:]
                if stderr_lines:
                    shared_console.print(
                        f"[red][livereload][stderr] Tail of {stderr_path}:\n"
                        + "".join(stderr_lines)
                    )
            except Exception as e:
                shared_console.print(f"[red][livereload][stderr] Error: {e}[/red]")
        if (not stdout_path or not stdout_lines) and (
            not stderr_path or not stderr_lines
        ):
            shared_console.print("[livereload] No output or errors captured in logs.")
