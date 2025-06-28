import requests
from bs4 import BeautifulSoup
from janito.tools.adapters.local.adapter import register_local_tool
from janito.tools.tool_base import ToolBase, ToolPermissions
from janito.report_events import ReportAction
from janito.i18n import tr
from janito.tools.tool_utils import pluralize


@register_local_tool
class FetchUrlTool(ToolBase):
    """
    Fetch the content of a web page and extract its text.

    Args:
        url (str): The URL of the web page to fetch.
        search_strings (list[str], optional): Strings to search for in the page content.
    Returns:
        str: Extracted text content from the web page, or a warning message. Example:
            - "<main text content...>"
            - "No lines found for the provided search strings."
            - "Warning: Empty URL provided. Operation skipped."
    """
    permissions = ToolPermissions(read=True)
    tool_name = "fetch_url"

    def run(self, url: str, search_strings: list[str] = None) -> str:
        if not url.strip():
            self.report_warning(tr("ℹ️ Empty URL provided."), ReportAction.READ)
            return tr("Warning: Empty URL provided. Operation skipped.")
        self.report_action(tr("🌐 Fetch URL '{url}' ...", url=url), ReportAction.READ)
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            status_code = http_err.response.status_code if http_err.response else None
            if status_code and 400 <= status_code < 500:
                self.report_error(
                    tr(
                        "❗ HTTP {status_code} error for URL: {url}",
                        status_code=status_code,
                        url=url,
                    ),
                    ReportAction.READ,
                )
                return tr(
                    "Warning: HTTP {status_code} error for URL: {url}",
                    status_code=status_code,
                    url=url,
                )
            else:
                self.report_error(
                    tr(
                        "❗ HTTP error for URL: {url}: {err}",
                        url=url,
                        err=str(http_err),
                    ),
                    ReportAction.READ,
                )
                return tr(
                    "Warning: HTTP error for URL: {url}: {err}",
                    url=url,
                    err=str(http_err),
                )
        except Exception as err:
            self.report_error(
                tr("❗ Error fetching URL: {url}: {err}", url=url, err=str(err)),
                ReportAction.READ,
            )
            return tr(
                "Warning: Error fetching URL: {url}: {err}", url=url, err=str(err)
            )
        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text(separator="\n")
        if search_strings:
            filtered = []
            for s in search_strings:
                idx = text.find(s)
                if idx != -1:
                    start = max(0, idx - 200)
                    end = min(len(text), idx + len(s) + 200)
                    snippet = text[start:end]
                    filtered.append(snippet)
            if filtered:
                text = "\n...\n".join(filtered)
            else:
                text = tr("No lines found for the provided search strings.")
        num_lines = len(text.splitlines())
        self.report_success(
            tr(
                "✅ {num_lines} {line_word}",
                num_lines=num_lines,
                line_word=pluralize("line", num_lines),
            ),
            ReportAction.READ,
        )
        return text
