import os
import shutil
from janito.tools.adapters.local.adapter import register_local_tool

from janito.tools.tool_utils import display_path
from janito.tools.tool_base import ToolBase
from janito.report_events import ReportAction
from janito.i18n import tr


@register_local_tool
class RemoveFileTool(ToolBase):
    """
    Remove a file at the specified path.

    Args:
        file_path (str): Path to the file to remove.
        backup (bool, optional): If True, create a backup (.bak) before removing. Recommend using backup=True only in the first call to avoid redundant backups. Defaults to False.
    Returns:
        str: Status message indicating the result. Example:
            - "			 Successfully removed the file at ..."
            - "			 Cannot remove file: ..."
    """

    tool_name = "remove_file"

    def run(self, file_path: str, backup: bool = False) -> str:
        original_path = file_path
        path = file_path  # Using file_path as is
        disp_path = display_path(original_path)
        backup_path = None
        # Report initial info about what is going to be removed
        self.report_action(
            tr("🗑️ Remove file '{disp_path}' ...", disp_path=disp_path),
            ReportAction.CREATE,
        )
        if not os.path.exists(path):
            self.report_error(tr("❌ File does not exist."), ReportAction.REMOVE)
            return tr("❌ File does not exist.")
        if not os.path.isfile(path):
            self.report_error(tr("❌ Path is not a file."), ReportAction.REMOVE)
            return tr("❌ Path is not a file.")
        try:
            if backup:
                backup_path = path + ".bak"
                shutil.copy2(path, backup_path)
            os.remove(path)
            self.report_success(tr("✅ File removed"), ReportAction.CREATE)
            msg = tr(
                "✅ Successfully removed the file at '{disp_path}'.",
                disp_path=disp_path,
            )
            if backup_path:
                msg += tr(
                    " (backup at {backup_disp})",
                    backup_disp=display_path(original_path + ".bak"),
                )
            return msg
        except Exception as e:
            self.report_error(
                tr("❌ Error removing file: {error}", error=e), ReportAction.REMOVE
            )
            return tr("❌ Error removing file: {error}", error=e)
