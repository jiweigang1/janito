from .base import ShellCmdHandler
from .edit import EditShellHandler
from .history_view import ViewShellHandler
from .lang import LangShellHandler
from .livelogs import LivelogsShellHandler
from .last import LastShellHandler
from .prompt import PromptShellHandler, RoleShellHandler, ProfileShellHandler
from .multi import MultiShellHandler
from .role import RoleCommandShellHandler
from .session import HistoryShellHandler
from .termweb_log import TermwebLogTailShellHandler
from .tools import ToolsShellHandler
from .help import HelpShellHandler
from janito.cli.console import shared_console

COMMAND_HANDLERS = {
    "/clear": __import__(
        "janito.cli.chat_mode.shell.commands.clear", fromlist=["ClearShellHandler"]
    ).ClearShellHandler,
    "/restart": __import__(
        "janito.cli.chat_mode.shell.commands.conversation_restart",
        fromlist=["RestartShellHandler"],
    ).RestartShellHandler,
    "/edit": EditShellHandler,
    "/view": ViewShellHandler,
    "/lang": LangShellHandler,
    "/livelogs": LivelogsShellHandler,
    "/last": LastShellHandler,
    "/prompt": PromptShellHandler,
    "/role": RoleShellHandler,
    "/profile": ProfileShellHandler,
    "/history": HistoryShellHandler,
    "/termweb-logs": TermwebLogTailShellHandler,
    "/tools": ToolsShellHandler,
    "/multi": MultiShellHandler,
    "/help": HelpShellHandler,
}


def get_shell_command_names():
    return sorted(cmd for cmd in COMMAND_HANDLERS.keys() if cmd.startswith("/"))


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
