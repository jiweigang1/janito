from janito.tools.tool_base import ToolBase
from janito.tools.adapters.local.adapter import register_local_tool
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
        if not os.path.exists(file_path):
            return "⚠️ Error: The specified file does not exist."
        
        if not file_path.lower().endswith('.html'):
            return "⚠️ Error: The specified file is not an HTML file."
        
        try:
            webbrowser.open(f"file://{os.path.abspath(file_path)}")
            return "✅ Opened."
        except Exception as e:
            return f"⚠️ Error: {str(e)}"