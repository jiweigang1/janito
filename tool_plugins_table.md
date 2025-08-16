# Tool Plugins - Detailed Table

## Complete Tool Organization by Plugin

| Plugin | Tool Name | Description | Category |
|--------|-----------|-------------|----------|
| **📁 File Manager** | `create_file` | Create new files with content | File Creation |
| **📁 File Manager** | `read_files` | Read multiple files at once | File Reading |
| **📁 File Manager** | `view_file` | Read specific lines or entire files | File Reading |
| **📁 File Manager** | `replace_text_in_file` | Find and replace text in files | File Modification |
| **📁 File Manager** | `validate_file_syntax` | Check file syntax (Python/Markdown) | File Validation |
| **📁 File Manager** | `create_directory` | Create new directories | Directory Operations |
| **📁 File Manager** | `remove_directory` | Remove directories (recursive option) | Directory Operations |
| **📁 File Manager** | `remove_file` | Delete single files | File Operations |
| **📁 File Manager** | `copy_file` | Copy files or directories | File Operations |
| **📁 File Manager** | `move_file` | Move/rename files or directories | File Operations |
| **📁 File Manager** | `find_files` | Search for files by pattern (respects .gitignore) | File Search |
| **🔍 Code Analyzer** | `get_file_outline` | Get file structure (classes, functions, etc.) | Code Analysis |
| **🔍 Code Analyzer** | `search_outline` | Search within file outlines | Code Analysis |
| **🔍 Code Analyzer** | `search_text` | Full-text search across files with regex support | Code Search |
| **🌐 Web Tools** | `fetch_url` | Download web pages with advanced options | Web Scraping |
| **🌐 Web Tools** | `open_url` | Open URLs in default browser | Web Browsing |
| **🌐 Web Tools** | `open_html_in_browser` | Open local HTML files in browser | Web Browsing |
| **🐍 Python Dev** | `python_code_run` | Execute Python code via stdin | Python Execution |
| **🐍 Python Dev** | `python_command_run` | Execute Python with -c flag | Python Execution |
| **🐍 Python Dev** | `python_file_run` | Run Python script files | Python Execution |
| **⚡ System Tools** | `run_powershell_command` | Execute PowerShell commands | System Operations |
| **📊 Visualization** | `read_chart` | Display charts in terminal (bar, line, pie, table) | Data Visualization |
| **💬 User Interface** | `ask_user` | Prompt user for input/clarification | User Interaction |

## Plugin Statistics

| Plugin | Tool Count | Percentage |
|--------|------------|------------|
| 📁 File Manager | 11 | 47.8% |
| 🔍 Code Analyzer | 3 | 13.0% |
| 🌐 Web Tools | 3 | 13.0% |
| 🐍 Python Dev | 3 | 13.0% |
| ⚡ System Tools | 1 | 4.3% |
| 📊 Visualization | 1 | 4.3% |
| 💬 User Interface | 1 | 4.3% |
| **Total** | **23** | **100%** |

## Quick Reference by Use Case

| When you need to... | Use Plugin | Specific Tool |
|---------------------|------------|---------------|
| Create a new file | 📁 File Manager | `create_file` |
| Search code across project | 🔍 Code Analyzer | `search_text` |
| Download a webpage | 🌐 Web Tools | `fetch_url` |
| Run Python code | 🐍 Python Dev | `python_code_run` |
| Execute system command | ⚡ System Tools | `run_powershell_command` |
| Show data in chart | 📊 Visualization | `read_chart` |
| Get user input | 💬 User Interface | `ask_user` |