import requests
import time
import os
import json
from pathlib import Path
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
        timeout (int, optional): Timeout in seconds for the HTTP request. Defaults to 10.
    Returns:
        str: Extracted text content from the web page, or a warning message. Example:
            - "<main text content...>"
            - "No lines found for the provided search strings."
            - "Warning: Empty URL provided. Operation skipped."
    """

    permissions = ToolPermissions(read=True)
    tool_name = "fetch_url"

    def __init__(self):
        super().__init__()
        self.cache_dir = Path.home() / ".janito" / "cache" / "fetch_url"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "error_cache.json"
        self._load_cache()

    def _load_cache(self):
        """Load error cache from disk."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.error_cache = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.error_cache = {}
        else:
            self.error_cache = {}

    def _save_cache(self):
        """Save error cache to disk."""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.error_cache, f, indent=2)
        except IOError:
            pass  # Silently fail if we can't write cache

    def _get_cached_error(self, url: str) -> tuple[str, bool]:
        """
        Check if we have a cached error for this URL.
        Returns (error_message, is_cached) tuple.
        """
        if url not in self.error_cache:
            return None, False
        
        entry = self.error_cache[url]
        current_time = time.time()
        
        # Different expiration times for different status codes
        if entry['status_code'] == 403:
            # Cache 403 errors for 24 hours (more permanent)
            expiration_time = 24 * 3600
        elif entry['status_code'] == 404:
            # Cache 404 errors for 1 hour (more temporary)
            expiration_time = 3600
        else:
            # Cache other 4xx errors for 30 minutes
            expiration_time = 1800
            
        if current_time - entry['timestamp'] > expiration_time:
            # Cache expired, remove it
            del self.error_cache[url]
            self._save_cache()
            return None, False
            
        return entry['message'], True

    def _cache_error(self, url: str, status_code: int, message: str):
        """Cache an HTTP error response."""
        self.error_cache[url] = {
            'status_code': status_code,
            'message': message,
            'timestamp': time.time()
        }
        self._save_cache()

    def _fetch_url_content(self, url: str, timeout: int = 10) -> str:
        """Fetch URL content and handle HTTP errors."""
        # Check cache first for known errors
        cached_error, is_cached = self._get_cached_error(url)
        if cached_error:
            self.report_warning(
                tr(
                    "ℹ️ Using cached HTTP error for URL: {url}",
                    url=url,
                ),
                ReportAction.READ,
            )
            return cached_error

        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            return response.text
        except requests.exceptions.HTTPError as http_err:
            status_code = http_err.response.status_code if http_err.response else None
            if status_code and 400 <= status_code < 500:
                error_message = tr(
                    "Warning: HTTP {status_code} error for URL: {url}",
                    status_code=status_code,
                    url=url,
                )
                # Cache 403 and 404 errors
                if status_code in [403, 404]:
                    self._cache_error(url, status_code, error_message)
                
                self.report_error(
                    tr(
                        "❗ HTTP {status_code} error for URL: {url}",
                        status_code=status_code,
                        url=url,
                    ),
                    ReportAction.READ,
                )
                return error_message
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
        timeout: int = 10,
    ) -> str:
        if not url.strip():
            self.report_warning(tr("ℹ️ Empty URL provided."), ReportAction.READ)
            return tr("Warning: Empty URL provided. Operation skipped.")

        self.report_action(tr("🌐 Fetch URL '{url}' ...", url=url), ReportAction.READ)

        # Fetch URL content
        html_content = self._fetch_url_content(url, timeout=timeout)
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
