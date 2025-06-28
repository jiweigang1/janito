"""
CLI Command: List supported LLM providers
"""

from janito.provider_registry import list_providers


def handle_list_providers(args=None):
    list_providers()
