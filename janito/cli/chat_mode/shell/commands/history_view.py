from janito.cli.console import shared_console
from janito.cli.chat_mode.shell.commands.base import ShellCmdHandler

class ViewShellHandler(ShellCmdHandler):
    help_text = "Print the current LLM conversation or agent driver history"

    def run(self):
        # Prefer agent's driver history if available
        agent = getattr(self.shell_state, 'agent', None)
        messages = None
        if agent and hasattr(agent, 'driver') and hasattr(agent.driver, 'get_history'):
            messages = agent.driver.get_history()
            if not messages:
                shared_console.print("[yellow]No history found in the agent's driver.[/yellow]")
                return
        else:
            # fallback
            messages = self.shell_state.conversation_history.get_history()
            if not messages:
                shared_console.print("[yellow]Conversation history is empty.[/yellow]")
                return
        for i, msg in enumerate(messages, 1):
            role = msg.get("role", "?")
            content = msg.get("content", "")
            metadata = msg.get("metadata")
            shared_console.print(f"[bold]{i}. {role}:[/bold] {content}")
            if metadata:
                shared_console.print(f"   [cyan]metadata:[/cyan] {metadata}")
