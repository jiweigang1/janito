# Plugin System Documentation

## Plugin Structure

```
plugins/
├── __init__.py                 # Main plugin registry
├── README.md                   # This documentation
├── core/                       # Core system plugins
│   ├── __init__.py
│   ├── filemanager/           # 📁 File Manager (11 tools)
│   │   └── __init__.py
│   ├── codeanalyzer/          # 🔍 Code Analyzer (3 tools)
│   │   └── __init__.py
│   └── system/                # ⚡ System Tools (1 tool)
│       └── __init__.py
├── web/                        # Web-related plugins
│   ├── __init__.py
│   └── webtools/              # 🌐 Web Tools (3 tools)
│       └── __init__.py
├── dev/                        # Development plugins
│   ├── __init__.py
│   ├── pythondev/             # 🐍 Python Dev (3 tools)
│   │   └── __init__.py
│   └── visualization/         # 📊 Visualization (1 tool)
│       └── __init__.py
└── ui/                         # User interface plugins
    ├── __init__.py
    └── userinterface/         # 💬 User Interface (1 tool)
        └── __init__.py
```

## Plugin Naming Convention

- **core.<name>**: Essential system tools
- **web.<name>**: Web scraping and browsing tools
- **dev.<name>**: Development-specific tools
- **ui.<name>**: User interaction tools

## Usage Examples

```python
# Import specific plugin
from plugins.core import filemanager
from plugins.web import webtools

# Use plugin functions
filemanager.create_file("test.py", "print('hello')")
webtools.fetch_url("https://example.com")

# Get plugin info
import plugins
print(plugins.list_plugins())
# Output: ['core.filemanager', 'core.codeanalyzer', 'core.system', ...]
```

## Plugin Metadata

Each plugin module contains:
- `__plugin_name__`: Full plugin name (e.g., "core.filemanager")
- `__plugin_description__`: Human-readable description
- `__plugin_tools__`: List of available tool functions

## Tool Distribution

| Plugin | Tools | Percentage |
|--------|-------|------------|
| core.filemanager | 11 | 47.8% |
| core.codeanalyzer | 3 | 13.0% |
| web.webtools | 3 | 13.0% |
| dev.pythondev | 3 | 13.0% |
| core.system | 1 | 4.3% |
| dev.visualization | 1 | 4.3% |
| ui.userinterface | 1 | 4.3% |
| **Total** | **23** | **100%** |