import webbrowser
from janito.tool_registry import register_tool
from janito.tool_base import ToolBase
from janito.report_events import ReportAction
from janito.i18n import tr


@register_tool(name="open_url")
class OpenUrlTool(ToolBase):
    """
    Open the supplied URL in the default web browser.
    Args:
        url (str): The URL to open.
    Returns:
        str: Status message indicating the result.
    """

    def run(self, url: str) -> str:
        if not url.strip():
            self.report_warning(tr("ℹ️ Empty URL provided."), ReportAction.OPEN)
            return tr("Warning: Empty URL provided. Operation skipped.")
        self.report_info(tr("🌐 Opening URL '{url}' ...", url=url), ReportAction.READ)
        try:
            webbrowser.open(url)
        except Exception as err:
            self.report_error(tr("❗ Error opening URL: {url}: {err}", url=url, err=str(err)), ReportAction.OPEN)
            return tr("Warning: Error opening URL: {url}: {err}", url=url, err=str(err))
        self.report_success(tr("✅ URL opened in browser: {url}", url=url), ReportAction.WRITE)
        return tr("URL opened in browser: {url}", url=url)
