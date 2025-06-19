import os
from janito.cli.chat_mode.shell.session.manager import reset_session_id
from janito.cli.chat_mode.shell.commands.base import ShellCmdHandler
from janito.cli.console import shared_console


def handle_restart(shell_state=None):
    from janito.cli.chat_mode.shell.session.manager import (
        load_last_conversation,
        save_conversation,
    )

    reset_session_id()
    save_path = os.path.join(".janito", "last_conversation.json")

    # --- Append end-of-conversation message to old history if it exists and is non-trivial ---
    if os.path.exists(save_path):
        try:
            messages, prompts, usage = load_last_conversation(save_path)
            if messages and (
                len(messages) > 1
                or (len(messages) == 1 and messages[0].get("role") != "system")
            ):
                messages.append(
                    {"role": "system", "content": "[Session ended by user]"}
                )
                # Save to permanent chat history (let save_conversation pick session file)
                save_conversation(messages, prompts, usage)
        except Exception as e:
            shared_console.print(
                f"[bold red]Failed to update previous conversation history:[/bold red] {e}"
            )

    # Clear the terminal screen
    shared_console.clear()

    # Reset conversation history using the agent's method
    if hasattr(shell_state, "agent") and shell_state.agent:
        shell_state.agent.reset_conversation_history()

    # Reset tool use tracker
    try:
        from janito.tools.tool_use_tracker import ToolUseTracker

        ToolUseTracker.instance().clear_history()
    except Exception as e:
        shared_console.print(
            f"[bold yellow]Warning: Failed to reset tool use tracker:[/bold yellow] {e}"
        )

    # Reset token usage info in-place so all references (including status bar) are updated
    for k in ("prompt_tokens", "completion_tokens", "total_tokens"):
        shell_state.last_usage_info[k] = 0
    shell_state.last_elapsed = None

    # Reset the performance collector's last usage (so toolbar immediately reflects cleared stats)
    try:
        from janito.perf_singleton import performance_collector

        performance_collector.reset_last_request_usage()
    except Exception as e:
        shared_console.print(
            f"[bold yellow]Warning: Failed to reset PerformanceCollector token info:[/bold yellow] {e}"
        )

    shared_console.print(
        "[bold green]Conversation history has been started (context reset).[/bold green]"
    )


handle_restart.help_text = "Start a new conversation (reset context)"


class RestartShellHandler(ShellCmdHandler):
    help_text = "Start a new conversation (reset context)"

    def run(self):
        handle_restart(self.shell_state)
