from janito.tools.adapters.local.adapter import register_local_tool

from janito.tools.tool_utils import display_path
from janito.tools.tool_base import ToolBase, ToolPermissions
from janito.report_events import ReportAction
from janito.i18n import tr
import os


@register_local_tool
class CreateDirectoryTool(ToolBase):
    """
    Create a new directory at the specified file_path.
    Args:
        file_path (str): Path for the new directory.
    Returns:
        str: Status message indicating the result. Example:
            - "5c5 Successfully created the directory at ..."
            - "5d7 Cannot create directory: ..."
    """
    permissions = ToolPermissions(write=True)
    tool_name = "create_directory"

    def run(self, file_path: str) -> str:
        # file_path = expand_path(file_path)
        # Using file_path as is
        disp_path = display_path(file_path)
        self.report_action(
            tr("📁 Create directory '{disp_path}' ...", disp_path=disp_path),
            ReportAction.CREATE,
        )
        try:
            if os.path.exists(file_path):
                if not os.path.isdir(file_path):
                    self.report_error(
                        tr(
                            "❌ Path '{disp_path}' exists and is not a directory.",
                            disp_path=disp_path,
                        )
                    )
                    return tr(
                        "❌ Path '{disp_path}' exists and is not a directory.",
                        disp_path=disp_path,
                    )
                self.report_error(
                    tr(
                        "❗ Directory '{disp_path}' already exists.",
                        disp_path=disp_path,
                    )
                )
                return tr(
                    "❗ Cannot create directory: '{disp_path}' already exists.",
                    disp_path=disp_path,
                )
            os.makedirs(file_path, exist_ok=True)
            self.report_success(tr("✅ Directory created"))
            return tr(
                "✅ Successfully created the directory at '{disp_path}'.",
                disp_path=disp_path,
            )
        except Exception as e:
            self.report_error(
                tr(
                    "❌ Error creating directory '{disp_path}': {error}",
                    disp_path=disp_path,
                    error=e,
                )
            )
            return tr("❌ Cannot create directory: {error}", error=e)
