"""
Agent and tool setup for Janito Chat CLI.
"""
from pathlib import Path
from janito.cli.provider_setup import setup_provider, setup_agent
from janito.tool_registry import ToolRegistry

class AgentSetup:
    def __init__(self, shell_state, conversation_history):
        self.shell_state = shell_state
        self.conversation_history = conversation_history
    def setup_agents(self, provider_instance):
        from janito.cli.config import config
        tool_registry = ToolRegistry()
        all_tool_classes = tool_registry.get_tool_classes()
        templates_dir = Path(__file__).parent.parent / 'agent' / 'templates' / 'profiles'
        main_template_path = str(templates_dir / 'system_prompt_template_main.txt.j2')
        main_agent = setup_agent(
            provider_instance,
            self.conversation_history,
            tools=all_tool_classes,
            template_path=main_template_path
        )
        self.shell_state.agent = main_agent
        self.shell_state.mode = 'main'
        self.shell_state.main_enabled = True
