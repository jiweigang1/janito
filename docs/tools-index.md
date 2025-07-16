# Tools Index

Janito provides a comprehensive set of tools for file operations, code execution, web access, and more. Tools can be selectively disabled using the [disabled tools configuration](guides/disabled-tools.md).

## Available Tools

### Web Tools

#### open_url

Opens the supplied URL or local file in the default web browser.

**Arguments:**

- `url` (str): The URL or local file path (as a file:// URL) to open. Supports both web URLs (http, https) and local files (file://).

**Returns:**

- Status message indicating the result.

**Example Usage:**

- Open a website: `open_url(url="https://example.com")`
- Open a local file: `open_url(url="file:///C:/path/to/file.html")`

This tool replaces the previous `open_html_in_browser` tool, and can be used for both web and local files.

### search_text

Search for a text query in files or directories.

**Arguments:**

- `paths` (str): Space-separated list of file or directory paths to search in.
- `query` (str): Text or regular expression to search for.
- `use_regex` (bool): Treat `query` as a regex pattern (default: False).
- `case_sensitive` (bool): Enable case-sensitive search (default: False).
- `max_depth` (int): Maximum directory depth to search (default: 0 = unlimited).
- `max_results` (int): Maximum matching lines to return (default: 100).
- `count_only` (bool): Return only match counts instead of lines (default: False).

**Returns:**

- Matching lines with file paths and line numbers, or match counts if `count_only=True`.

**Example Usage:**

- Plain-text search: `search_text(paths="src", query="TODO")`
- Regex search: `search_text(paths="src tests", query=r"def\s+\w+", use_regex=True)`
- Case-insensitive count: `search_text(paths="docs", query="janito", case_sensitive=False, count_only=True)`

## Tool Management

### Disabling Tools

You can disable specific tools using configuration:

```bash
# Disable interactive prompts
janito --set disabled_tools=ask_user

# Disable code execution
janito --set disabled_tools=python_code_run,run_powershell_command

# View current disabled tools and config file path
janito --show-config
```

### Listing Available Tools

See all currently available tools:

```bash
janito --list-tools
```

For complete documentation on tool disabling, see the [Disabling Tools Guide](guides/disabled-tools.md).
