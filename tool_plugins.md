# Tool Plugins Organization

## 📁 File Manager Plugin

**Purpose**: Core file and directory operations

- `create_file` - Create new files with content
- `read_files` - Read multiple files at once
- `view_file` - Read specific lines or entire files
- `replace_text_in_file` - Find and replace text in files
- `validate_file_syntax` - Check file syntax (Python/Markdown)
- `create_directory` - Create new directories
- `remove_directory` - Remove directories (recursive option)
- `remove_file` - Delete single files
- `copy_file` - Copy files or directories
- `move_file` - Move/rename files or directories
- `find_files` - Search for files by pattern (respects .gitignore)

## 🔍 Code Analyzer Plugin

**Purpose**: Code analysis and structure understanding

- `get_file_outline` - Get file structure (classes, functions, etc.)
- `search_outline` - Search within file outlines
- `search_text` - Full-text search across files with regex support

## 🌐 Web Tools Plugin

**Purpose**: Web scraping, browsing, and URL operations

- `fetch_url` - Download web pages with advanced options
- `open_url` - Open URLs in default browser
- `open_html_in_browser` - Open local HTML files in browser

## 🐍 Python Dev Plugin

**Purpose**: Python development and execution

- `python_code_run` - Execute Python code via stdin
- `python_command_run` - Execute Python with -c flag
- `python_file_run` - Run Python script files

## ⚡ System Tools Plugin

**Purpose**: System-level operations and shell access

- `run_powershell_command` - Execute PowerShell commands

## 📊 Visualization Plugin

**Purpose**: Data visualization and charts

- `read_chart` - Display charts in terminal (bar, line, pie, table)

## 💬 User Interface Plugin

**Purpose**: User interaction and input

- `ask_user` - Prompt user for input/clarification

---

## Plugin Usage Summary

| Plugin | Primary Use Cases |
|--------|-------------------|
| **File Manager** | Creating, reading, modifying, organizing files and directories |
| **Code Analyzer** | Understanding code structure, searching codebases |
| **Web Tools** | Web scraping, API testing, browser automation |
| **Python Dev** | Running Python code, testing scripts, development workflows |
| **System Tools** | System administration, shell scripting, automation |
| **Visualization** | Data analysis, reporting, progress tracking |
| **User Interface** | Interactive workflows, user confirmations, dynamic input |