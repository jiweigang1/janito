"""
CLI Command: List available LLM drivers and their dependencies
"""

import importlib
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

console = Console()


def get_driver_info():
    """Get information about all available drivers."""
    drivers = []
    
    # Define known driver modules
    driver_modules = [
        ("janito.drivers.openai.driver", "OpenAIModelDriver"),
        ("janito.drivers.azure_openai.driver", "AzureOpenAIModelDriver"),
        ("janito.drivers.zai.driver", "ZAIModelDriver"),
    ]
    
    for module_path, class_name in driver_modules:
        try:
            # Import the module
            module = importlib.import_module(module_path)
            driver_class = getattr(module, class_name)
            
            # Get availability info
            available = getattr(driver_class, 'available', True)
            unavailable_reason = getattr(driver_class, 'unavailable_reason', None)
            
            # Get dependencies from module imports
            dependencies = []
            module_file = Path(module.__file__)
            
            # Read module file to detect imports
            with open(module_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Simple dependency detection
            if 'import openai' in content or 'from openai' in content:
                dependencies.append('openai')
            if 'import zai' in content or 'from zai' in content:
                dependencies.append('zai')
            if 'import anthropic' in content or 'from anthropic' in content:
                dependencies.append('anthropic')
            if 'import google' in content or 'from google' in content:
                dependencies.append('google-generativeai')
            
            # Check if dependencies are available
            dep_status = []
            for dep in dependencies:
                try:
                    importlib.import_module(dep)
                    dep_status.append(f"✅ {dep}")
                except ImportError:
                    dep_status.append(f"❌ {dep}")
            
            if not dependencies:
                dep_status = ["No external dependencies"]
            
            drivers.append({
                'name': class_name,
                'available': available,
                'reason': unavailable_reason,
                'dependencies': dep_status
            })
            
        except (ImportError, AttributeError) as e:
            drivers.append({
                'name': class_name,
                'module': module_path,
                'available': False,
                'reason': str(e),
                'dependencies': ["❌ Module not found"]
            })
    
    return drivers


def handle_list_drivers(args=None):
    """List all available LLM drivers with their status and dependencies."""
    drivers = get_driver_info()
    
    if not drivers:
        console.print("[red]No drivers found[/red]")
        return
    
    # Create table
    table = Table(title="Available LLM Drivers")
    table.add_column("Driver", style="cyan", no_wrap=True)
    table.add_column("Status", style="bold")
    table.add_column("Dependencies", style="yellow")
    
    for driver in drivers:
        name = driver['name']
        
        if driver['available']:
            status = "[green]✅ Available[/green]"
            if driver['reason']:
                status = f"[yellow]⚠️ Available ({driver['reason']})[/yellow]"
        else:
            status = f"[red]❌ Unavailable[/red]"
            if driver['reason']:
                status = f"[red]❌ {driver['reason']}[/red]"
        
        deps = "\n".join(driver['dependencies'])
        
        table.add_row(name, status, deps)
    
    console.print(table)
    
    # Installation help
    console.print("\n[dim]💡 Install missing deps: pip install openai zai anthropic google-generativeai[/dim]")


if __name__ == "__main__":
    handle_list_drivers()