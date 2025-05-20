"""
PromptHandler: Handles prompt submission and response formatting for janito CLI (one-shot prompt execution).
"""
import time
from janito.version import __version__ as VERSION
from janito.cli.provider_setup import setup_main_agent
from janito.cli.utils import format_tokens, format_generation_time
from janito.cli.prompt_handler import PromptHandler as GenericPromptHandler
from janito.cli.single_shot_mode.output import print_verbose_header, print_performance, handle_exception
from janito.cli.agent_utils import build_cli_agent_and_history
import janito.tools  # Ensure all tools are registered

class PromptHandler:
    def __init__(self, args):
        self.args = args
        # Unified agent and conversation history setup
        provider_instance, conversation_history, agent = build_cli_agent_and_history(self.args)
        self.generic_handler = GenericPromptHandler(args, conversation_history, provider_instance=provider_instance)
        self.generic_handler.agent = agent

    def handle(self) -> None:
        # setup_main_agent creates an agent, skipping shell state (for one-shot mode)
        from janito.cli.provider_setup import setup_main_agent
        self.generic_handler.agent = setup_main_agent(self.args, self.generic_handler.conversation_history)
        self.generic_handler.handle_prompt(
            self.args.user_prompt,
            args=self.args,
            print_header=True,
            raw=getattr(self.args, 'raw', False)
        )
        # Performance printing removed with timing
