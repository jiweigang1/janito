import os
import webbrowser
from janito.tools.adapters.local.adapter import register_local_tool
from janito.tools.tool_base import ToolBase, ToolPermissions
from janito.report_events import ReportAction
from janito.i18n import tr

@register_local_tool
class OpenHtmlInBrowserTool(ToolBase):
    """
    Open the supplied HTML file in the default web browser.

    Args:
        file_path (str): Path to the HTML file to open.
    Returns:
        str: Status message indicating the result.
    """
    permissions = ToolPermissions(read=True)
    tool_name = "open_html_in_browser"

    def run(self, file_path: str) -> str:
        if not file_path.strip():
            self.report_warning(tr("ℹ️ Empty file path provided."))
            return tr("Warning: Empty file path provided. Operation skipped.")
        if not os.path.isfile(file_path):
            self.report_error(tr("❗ File does not exist: {file_path}", file_path=file_path))
            return tr("Warning: File does not exist: {file_path}", file_path=file_path)
        if not file_path.lower().endswith(('.html', '.htm')):
            self.report_warning(tr("⚠️ Not an HTML file: {file_path}", file_path=file_path))
            return tr("Warning: Not an HTML file: {file_path}", file_path=file_path)
        url = 'file://' + os.path.abspath(file_path)
        self.report_action(tr("📖 Opening HTML file in browser: {file_path}", file_path=file_path), ReportAction.READ)
        try:
            webbrowser.open(url)
        except Exception as err:
            self.report_error(tr("❗ Error opening HTML file: {file_path}: {err}", file_path=file_path, err=str(err)))
            return tr("Warning: Error opening HTML file: {file_path}: {err}", file_path=file_path, err=str(err))
        self.report_success(tr("✅ HTML file opened in browser: {file_path}", file_path=file_path))
        return tr("HTML file opened in browser: {file_path}", file_path=file_path)
