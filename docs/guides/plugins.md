# Plugin System Guide

The janito plugin system allows you to extend the functionality of janito with custom tools, commands, and features.

## Overview

The plugin system consists of:

- **Plugin**: Base class for all plugins
- **PluginManager**: Manages plugin loading, registration, and lifecycle
- **Plugin Discovery**: Automatically finds and loads plugins from various locations

## Creating a Plugin

### Basic Plugin Structure

Create a new Python file or directory for your plugin:

```python
from janito.plugins.base import Plugin, PluginMetadata
from janito.tools.tool_base import ToolBase, ToolPermissions

class MyTool(ToolBase):
    tool_name = "my_tool"
    permissions = ToolPermissions(read=True, write=False, execute=True)
    
    def run(self, message: str) -> str:
        return f"Hello {message}!"

class MyPlugin(Plugin):
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="my_plugin",
            version="1.0.0",
            description="My custom plugin",
            author="Your Name",
            license="MIT"
        )
    
    def get_tools(self):
        return [MyTool]
    
    def initialize(self):
        print("My plugin initialized!")
```

### Plugin Locations

Plugins can be placed in:

1. `./plugins/` (project directory)
2. `~/.janito/plugins/` (user directory)
3. Any directory added via configuration

### Directory Structure

**Single file plugin:**
```
plugins/
└── my_plugin.py
```

**Package plugin:**
```
plugins/
└── my_plugin/
    ├── __init__.py
    └── plugin.py
```

## Configuration

### Enable Plugins

Add to your `janito.json`:

```json
{
  "plugins": {
    "paths": ["./plugins", "~/.janito/plugins"],
    "load": {
      "my_plugin": true,
      "another_plugin": {"setting": "value"}
    }
  }
}
```

### Plugin Configuration

Plugins can accept configuration:

```json
{
  "plugins": {
    "load": {
      "my_plugin": {
        "api_key": "secret",
        "debug": true
      }
    }
  }
}
```

## CLI Commands

### List Plugins

```bash
# List loaded plugins
janito --list-plugins

# List available plugins
janito --list-plugins-available
```

### Manual Loading

```python
from janito.plugins.manager import PluginManager

manager = PluginManager()
manager.load_plugin("my_plugin")
manager.load_plugin("my_plugin", {"config": "value"})
```

## Plugin Features

### Tools

Plugins can provide new tools by implementing `get_tools()`:

```python
def get_tools(self):
    return [MyTool1, MyTool2, MyTool3]
```

### Commands

Plugins can provide CLI commands:

```python
def get_commands(self):
    return {
        "my_command": self.handle_my_command
    }
```

### Configuration Schema

Define configuration validation:

```python
def get_config_schema(self):
    return {
        "type": "object",
        "properties": {
            "api_key": {"type": "string"},
            "debug": {"type": "boolean"}
        },
        "required": ["api_key"]
    }

def validate_config(self, config):
    return "api_key" in config
```

## Example Plugin

See `plugins/example_plugin.py` for a complete example including:

- Custom tools
- Configuration handling
- Initialization and cleanup

## Best Practices

1. **Naming**: Use descriptive plugin names
2. **Versioning**: Follow semantic versioning
3. **Dependencies**: List all dependencies in metadata
4. **Error Handling**: Handle configuration errors gracefully
5. **Documentation**: Provide clear descriptions and examples

## Troubleshooting

### Plugin Not Found

Check:

- Plugin file exists in search paths
- Plugin class inherits from `Plugin`
- File has correct extension (.py)

### Configuration Issues

- Validate configuration using `validate_config()`
- Check JSON schema with `get_config_schema()`
- Use debug logging to trace issues

### Tool Registration Issues

- Ensure tools inherit from `ToolBase`
- Set proper `tool_name` and `permissions`
- Implement required `run()` method

### Remote Plugin Issues

For issues with remote plugins from the `ikignosis/janito-plugins` repository, see the [Remote Plugins Guide](remote-plugins.md) for specific troubleshooting steps.