from typing import List
from janito.tool_base import ToolBase
from janito.report_events import ReportAction
from janito.tool_registry import register_tool
from janito.i18n import tr
import questionary
from questionary import Style

custom_style = Style(
    [
        ("pointer", "fg:#ffffff bg:#1976d2 bold"),
        ("highlighted", "fg:#ffffff bg:#1565c0 bold"),
        ("answer", "fg:#1976d2 bold"),
        ("qmark", "fg:#1976d2 bold"),
    ]
)
HAND_EMOJI = "590",