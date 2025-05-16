from .base import ShellCmdHandler
from .edit import EditHandler
from .history_view import ViewHandler
from .lang import LangHandler
from .livelogs import LivelogsHandler
from .last import LastHandler
from .prompt import PromptHandler, RoleHandler, ProfileHandler
from .role import RoleCommand
from .session import HistoryHandler
from .termweb_log import TermwebLogTailHandler
from .tools import ToolsHandler
from .help import HelpHandler
from janito.cli.console import shared_console

COMMAND_HANDLERS = {
    "/restart": __import__("janito.cli.chat_mode.shell.commands.conversation_restart", fromlist=["RestartHandler"]).RestartHandler,
    "/edit": EditHandler,
    "/view": ViewHandler,
    "/lang": LangHandler,
    "/livelogs": LivelogsHandler,
    "/last": LastHandler,
    "/prompt": PromptHandler,
    "/role": RoleHandler,
    "/profile": ProfileHandler,
    "/history": HistoryHandler,
    "/termweb-logs": TermwebLogTailHandler,
    "/tools": ToolsHandler,
    "/help": HelpHandler,
}

def handle_command(command, shell_state=None):
    parts = command.strip().split(maxsplit=1)
    cmd = parts[0]
    after_cmd_line = parts[1] if len(parts) > 1 else ""
    handler_cls = COMMAND_HANDLERS.get(cmd)
    if handler_cls:
        handler = handler_cls(after_cmd_line=after_cmd_line, shell_state=shell_state)
        return handler.run()
    shared_console.print(
        f"[bold red]Invalid command: {cmd}. Type /help for a list of commands.[/bold red]"
    )
    return None
