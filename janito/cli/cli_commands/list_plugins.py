"""
CLI command to list available and loaded plugins.
"""

import argparse
from typing import List, Dict, Any
from janito.plugins.discovery import list_available_plugins, discover_plugins
import os
from janito.plugins.manager import PluginManager


def handle_list_plugins(args: argparse.Namespace) -> None:
    """List plugins command handler."""
    
    if getattr(args, 'list_plugins_available', False):
        # List available plugins
        available = list_available_plugins()
        if available:
            print("Available plugins:")
            for plugin in available:
                print(f"  - {plugin}")
        else:
            print("No plugins found in search paths")
            print("Search paths:")
            print(f"  - {os.getcwd()}/plugins")
            print(f"  - {os.path.expanduser('~')}/.janito/plugins")
    else:
        # List loaded plugins
        manager = PluginManager()
        loaded = manager.list_plugins()
        
        if loaded:
            print("Loaded plugins:")
            for plugin_name in loaded:
                metadata = manager.get_plugin_metadata(plugin_name)
                if metadata:
                    print(f"  - {metadata.name} v{metadata.version}")
                    print(f"    {metadata.description}")
                    if metadata.author:
                        print(f"    Author: {metadata.author}")
                    print()
        else:
            print("No plugins loaded")


