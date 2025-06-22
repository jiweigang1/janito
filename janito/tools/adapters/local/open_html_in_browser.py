from janito.tools.tool_base import ToolBase
from janito.tools.adapters.local.adapter import register_local_tool
from janito.report_events import ReportAction
import webbrowser
import os

@register_local_tool
class OpenHtmlInBrowserTool(ToolBase):
    """
    Opens an HTML file in the default web browser.

    Args:
        file_path (str): The path to the HTML file to open.

    Returns:
        str: Status message indicating the result. Example:
            - "✅ Successfully opened the file in the default browser."
            - "⚠️ Error: The specified file does not exist."
            - "⚠️ Error: The specified file is not an HTML file."
    """

    tool_name = "open_html_in_browser"

    def run(self, file_path: str) -> str:
        from janito.i18n import tr
        disp_path = file_path
        self.report_action(tr("📖 Opening HTML file: '{disp_path}'", disp_path=disp_path), ReportAction.EXECUTE)

        if not os.path.exists(file_path):
            self.report_error(tr("⚠️ The specified file does not exist: '{disp_path}'", disp_path=disp_path))
            return "⚠️ The specified file does not exist."

        if not file_path.lower().endswith('.html'):
            self.report_error(tr("⚠️ The specified file is not an HTML file: '{disp_path}'", disp_path=disp_path))
            return "⚠️ The specified file is not an HTML file."

        try:
            webbrowser.open(f"file://{os.path.abspath(file_path)}")
            self.report_success(tr("✅ Ok"))
            return "✅ Ok"
        except Exception as e:
            self.report_error(tr("⚠️ Failed to open the HTML file: {err}", err=str(e)))
            return f"⚠️ Failed to open the file: {str(e)}"
