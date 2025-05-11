from janito.tool_registry import register_tool

# from janito.agent.tools_utils.expand_path import expand_path
from janito.tool_utils import display_path
from janito.tool_base import ToolBase
from janito.report_events import ReportAction
from janito.i18n import tr
import os


@register_tool(name="create_directory")
class CreateDirectoryTool(ToolBase):
    """
    Create a new directory at the specified file_path.
    Args:
        file_path (str): Path for the new directory.
    Returns:
        str: Status message indicating the result. Example:
            - "✅ Successfully created the directory at ..."
            - "❗ Cannot create directory: ..."
    """

    def run(self, file_path: str) -> str:
        # file_path = expand_path(file_path)
        # Using file_path as is
        disp_path = display_path(file_path)
        self.report_info(
            tr("📁 Create directory '{disp_path}' ...", disp_path=disp_path),
            ReportAction.WRITE,
        )
        try:
            if os.path.exists(file_path):
                if not os.path.isdir(file_path):
                    self.report_error(
                        tr(
                            "❌ Path '{disp_path}' exists and is not a directory.",
                            disp_path=disp_path,
                        ),
                        ReportAction.CREATE,
                    )
                    return tr(
                        "❌ Path '{disp_path}' exists and is not a directory.",
                        disp_path=disp_path,
                    )
                self.report_error(
                    tr(
                        "❗ Directory '{disp_path}' already exists.",
                        disp_path=disp_path,
                    ),
                    ReportAction.CREATE,
                )
                return tr(
                    "❗ Cannot create directory: '{disp_path}' already exists.",
                    disp_path=disp_path,
                )
            os.makedirs(file_path, exist_ok=True)
            self.report_success(tr("✅ Directory created"), ReportAction.WRITE)
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
                ),
                ReportAction.CREATE,
            )
            return tr("❌ Cannot create directory: {error}", error=e)
