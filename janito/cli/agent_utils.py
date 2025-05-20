"""
This module provides utilities for agent and conversation history setup for CLI modes.
"""
from janito.cli.provider_setup import setup_provider, setup_main_agent
from janito.conversation_history import LLMConversationHistory

def build_cli_agent_and_history(args, config=None):
    """
    Set up and return a (provider_instance, conversation_history, agent) tuple for CLI modes.
    :param args: CLI arguments (for agent/model/provider selection)
    :param config: Optional config instance (for chat mode override)
    """
    conversation_history = LLMConversationHistory()
    provider_instance = setup_provider() # Uses global config
    agent = setup_main_agent(args, conversation_history)
    return provider_instance, conversation_history, agent
