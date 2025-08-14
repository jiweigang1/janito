"""
Base classes for janito plugins.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Type
from janito.tools.tool_base import ToolBase


@dataclass
class PluginMetadata:
    """Metadata describing a plugin."""
    name: str
    version: str
    description: str
    author: str
    license: str = "MIT"
    homepage: Optional[str] = None
    dependencies: List[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class Plugin(ABC):
    """
    Base class for all janito plugins.
    
    Plugins can provide tools, commands, or other functionality.
    """
    
    def __init__(self):
        self.metadata: PluginMetadata = self.get_metadata()
    
    @abstractmethod
    def get_metadata(self) -> PluginMetadata:
        """Return metadata describing this plugin."""
        pass
    
    def get_tools(self) -> List[Type[ToolBase]]:
        """
        Return a list of tool classes provided by this plugin.
        
        Returns:
            List of ToolBase subclasses that should be registered
        """
        return []
    
    def get_commands(self) -> Dict[str, Any]:
        """
        Return a dictionary of CLI commands provided by this plugin.
        
        Returns:
            Dict mapping command names to command handlers
        """
        return {}
    
    def initialize(self) -> None:
        """
        Called when the plugin is loaded.
        Override to perform any initialization needed.
        """
        pass
    
    def cleanup(self) -> None:
        """
        Called when the plugin is unloaded.
        Override to perform any cleanup needed.
        """
        pass
    
    def get_config_schema(self) -> Dict[str, Any]:
        """
        Return JSON schema for plugin configuration.
        
        Returns:
            JSON schema dict describing configuration options
        """
        return {}
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate plugin configuration.
        
        Args:
            config: Configuration dict to validate
            
        Returns:
            True if configuration is valid
        """
        return True