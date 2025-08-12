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
        max_length (int, optional): Maximum number of characters to return. Defaults to 5000.
        max_lines (int, optional): Maximum number of lines to return. Defaults to 200.
        context_chars (int, optional): Characters of context around search matches. Defaults to 400.
    Returns:
        str: Extracted text content from the web page, or a warning message. Example:
            - "<main text content...>"
            - "No lines found for the provided search strings."
            - "Warning: Empty URL provided. Operation skipped."
    """

    permissions = ToolPermissions(read=True)
    tool_name = "fetch_url"

    def _fetch_url_content(self, url: str) -> str:
        """Fetch URL content and handle HTTP errors."""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.text
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

    def _extract_and_clean_text(self, html_content: str) -> str:
        """Extract and clean text from HTML content."""
        soup = BeautifulSoup(html_content, "html.parser")
        text = soup.get_text(separator="\n")

        # Clean up excessive whitespace
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return "\n".join(lines)

    def _filter_by_search_strings(
        self, text: str, search_strings: list[str], context_chars: int
    ) -> str:
        """Filter text by search strings with context."""
        filtered = []
        for s in search_strings:
            idx = text.find(s)
            if idx != -1:
                start = max(0, idx - context_chars)
                end = min(len(text), idx + len(s) + context_chars)
                snippet = text[start:end]
                filtered.append(snippet)

        if filtered:
            return "\n...\n".join(filtered)
        else:
            return tr("No lines found for the provided search strings.")

    def _apply_limits(self, text: str, max_length: int, max_lines: int) -> str:
        """Apply length and line limits to text."""
        # Apply length limit
        if len(text) > max_length:
            text = text[:max_length] + "\n... (content truncated due to length limit)"

        # Apply line limit
        lines = text.splitlines()
        if len(lines) > max_lines:
            text = (
                "\n".join(lines[:max_lines])
                + "\n... (content truncated due to line limit)"
            )

        return text

    def run(
        self,
        url: str,
        search_strings: list[str] = None,
        max_length: int = 5000,
        max_lines: int = 200,
        context_chars: int = 400,
    ) -> str:
        if not url.strip():
            self.report_warning(tr("ℹ️ Empty URL provided."), ReportAction.READ)
            return tr("Warning: Empty URL provided. Operation skipped.")

        self.report_action(tr("🌐 Fetch URL '{url}' ...", url=url), ReportAction.READ)

        # Fetch URL content
        html_content = self._fetch_url_content(url)
        if html_content.startswith("Warning:"):
            return html_content

        # Extract and clean text
        text = self._extract_and_clean_text(html_content)

        # Filter by search strings if provided
        if search_strings:
            text = self._filter_by_search_strings(text, search_strings, context_chars)

        # Apply limits
        text = self._apply_limits(text, max_length, max_lines)

        # Report success
        num_lines = len(text.splitlines())
        total_chars = len(text)
        self.report_success(
            tr(
                "✅ {num_lines} {line_word}, {chars} chars",
                num_lines=num_lines,
                line_word=pluralize("line", num_lines),
                chars=total_chars,
            ),
            ReportAction.READ,
        )
        return text
