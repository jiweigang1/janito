from janito.cli.config import config
from janito.cli.chat_mode.shell.commands.base import ShellCmdHandler
from janito.cli.console import shared_console


class PromptShellHandler(ShellCmdHandler):
    help_text = "Show the system prompt"

    def run(self):
        agent = getattr(self.shell_state, "agent", None)
        if agent and hasattr(agent, "get_system_prompt"):
            prompt = agent.get_system_prompt()
            shared_console.print(
                f"[bold magenta]System Prompt:[/bold magenta]\n{prompt}"
            )
        else:
            shared_console.print(
                "[bold red]No LLM agent available to fetch the system prompt.[/bold red]"
            )


class RoleShellHandler(ShellCmdHandler):
    help_text = "Change the system role"

    def run(self):
        new_role = self.after_cmd_line.strip()
        if not new_role:
            agent = getattr(self.shell_state, "agent", None)
            if agent and hasattr(agent, "template_vars"):
                current_role = agent.template_vars.get("role", None)
            else:
                current_role = None
            if not current_role:
                current_role = "<not set>"
            shared_console.print(
                f"[bold green]Current system role:[/bold green] {current_role}"
            )
            return

        agent = getattr(self.shell_state, "agent", None)
        if agent and hasattr(agent, "set_template_var"):
            agent.set_template_var("role", new_role)
            # Refresh the system prompt with the new role if possible
            if (
                hasattr(agent, "set_system_using_template")
                and hasattr(agent, "_system_prompt_template_file")
                and agent._system_prompt_template_file
            ):
                agent.set_system_using_template(
                    agent._system_prompt_template_file, **agent.template_vars
                )
        shared_console.print(
            f"[bold green]System role updated to:[/bold green] {new_role}"
        )


class ProfileShellHandler(ShellCmdHandler):
    help_text = (
        "Show the current and available Agent Profile (only 'base' is supported)"
    )

    def run(self):
        shared_console.print("[bold green]Current profile:[/bold green] base")
        shared_console.print("[bold yellow]Available profiles:[/bold yellow]\n- base")
