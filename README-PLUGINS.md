# Janito Plugin System

A flexible plugin system for extending janito's functionality.

## Quick Start

1. **Create a plugin:**
   ```python
   # plugins/hello_plugin.py
   from janito.plugins.base import Plugin, PluginMetadata
   from janito.tools.tool_base import ToolBase, ToolPermissions

   class HelloTool(ToolBase):
       tool_name = "hello"
       permissions = ToolPermissions(read=True, write=False, execute=True)
       
       def run(self, name="World"):
           return f"Hello, {name}!"

   class HelloPlugin(Plugin):
       def get_metadata(self):
           return PluginMetadata(
               name="hello",
               version="1.0.0",
               description="A simple greeting plugin",
               author="You"
           )
       
       def get_tools(self):
           return [HelloTool]
   ```

2. **Enable the plugin:**
   ```json
   // janito.json
   {
     "plugins": {
       "load": {
         "hello": true
       }
     }
   }
   ```

3. **Use the plugin:**
   ```bash
   janito --list-plugins
   janito "Use the hello tool to greet Alice"
   ```

## Features

- **Dynamic Tool Registration**: Add new tools without modifying core code
- **Configuration Support**: Plugins can accept runtime configuration
- **Hot Loading**: Load/unload plugins at runtime
- **Multiple Sources**: Load from files, directories, or installed packages
- **Validation**: Built-in configuration validation and error handling

## Documentation

- [Plugin System Guide](docs/guides/plugins.md) - Complete documentation
- [Remote Plugins Guide](docs/guides/remote-plugins.md) - Using plugins from remote repositories
- [Example Plugin](plugins/example_plugin.py) - Working example
- [API Reference](docs/reference/plugins.md) - Technical details

## Development

See `tests/test_plugin_system.py` for comprehensive test examples.