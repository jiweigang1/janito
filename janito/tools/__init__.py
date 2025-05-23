from . import ask_user
from . import create_directory
from . import create_file
from . import copy_file
from . import fetch_url
from . import open_url
from . import find_files
from . import get_lines
from .get_file_outline import core  # noqa: F401,F811
from . import move_file
from .validate_file_syntax import core  # noqa: F401,F811
from . import remove_directory
from . import remove_file
from . import replace_text_in_file
from . import run_bash_command
from . import run_powershell_command
from . import search_text
from . import python_command_run
from . import python_file_run
from . import python_code_run

from janito.platform_discovery import PlatformDiscovery
from janito.tool_registry import ToolRegistry

# Start with all tool exports in a list
_tool_exports = [
    "ask_user",
    "create_directory",
    "create_file",
    "copy_file",
    "fetch_url",
    "open_url",
    "find_files",
    "GetFileOutlineTool",
    "get_lines",
    "move_file",
    "validate_file_syntax",
    "remove_directory",
    "remove_file",
    "replace_text_in_file",
    "run_bash_command",
    "run_powershell_command",
    "search_text",
    "python_command_run",
    "python_file_run",
    "python_code_run",
]

# Remove run_bash_command if powershell is available and not in git bash
pd = PlatformDiscovery()
registry = ToolRegistry()

def powershell_available():
    return bool(pd._detect_powershell())

def in_git_bash():
    return bool(pd._detect_git_bash())

_disable_bash = powershell_available() and not in_git_bash()

if _disable_bash:
    registry.disable_tool("run_bash_command")
    try:
        _tool_exports.remove("run_bash_command")
    except ValueError:
        pass

__all__ = _tool_exports
