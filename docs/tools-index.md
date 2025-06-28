# Tools Index

## open_url

**Description:**
Opens the supplied URL or local file in the default web browser.

**Arguments:**
- `url` (str): The URL or local file path (as a file:// URL) to open. Supports both web URLs (http, https) and local files (file://).

**Returns:**
- Status message indicating the result.

**Example Usage:**
- Open a website: `open_url(url="https://example.com")`
- Open a local file: `open_url(url="file:///C:/path/to/file.html")`

This tool replaces the previous `open_html_in_browser` tool, and can be used for both web and local files.
