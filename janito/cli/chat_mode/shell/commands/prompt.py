from janito.cli.config import config
from janito.cli.chat_mode.shell.commands.base import ShellCmdHandler
from janito.cli.console import shared_console

class PromptShellHandler(ShellCmdHandler):
    help_text = "Show the system prompt"

    def run(self):
        agent = getattr(self.shell_state, "agent", None)
        if agent and hasattr(agent, "get_system_prompt"):
            prompt = agent.get_system_prompt()
            shared_console.print(f"[bold magenta]System Prompt:[/bold magenta]\n{prompt}")
        else:
            shared_console.print("[bold red]No LLM agent available to fetch the system prompt.[/bold red]")

class RoleShellHandler(ShellCmdHandler):
    help_text = "Change the system role"

    def run(self):
        new_role = self.after_cmd_line.strip()
        if not new_role:
            current_role = config.get('role', '<not set>')
            shared_console.print(f"[bold green]Current system role:[/bold green] {current_role}")
            return
        config.set("role", new_role, runtime=True)
        agent = getattr(self.shell_state, "agent", None)
        if agent and hasattr(agent, "set_template_var"):
            agent.set_template_var("role", new_role)
        shared_console.print(f"[bold green]System role updated to:[/bold green] {new_role}")

class ProfileShellHandler(ShellCmdHandler):
    help_text = "Show the current and available Agent Profile (only 'base' is supported)"

    def run(self):
        shared_console.print("[bold green]Current profile:[/bold green] base")
        shared_console.print("[bold yellow]Available profiles:[/bold yellow]\n- base")
