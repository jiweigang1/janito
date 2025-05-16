"""
PromptHandler: Handles prompt submission and response formatting for janito CLI (one-shot prompt execution).
"""
import time
from janito.version import __version__ as VERSION
from janito.cli.provider_setup import setup_main_agent
from janito.cli.utils import format_tokens, format_generation_time
from janito.cli.prompt_handler import PromptHandler as GenericPromptHandler
from janito.cli.one_shot_mode.output import print_verbose_header, print_performance, handle_exception
import janito.tools  # Ensure all tools are registered

class PromptHandler:
    def __init__(self, args):
        self.args = args
        from janito.conversation_history import LLMConversationHistory
        self.generic_handler = GenericPromptHandler(args, LLMConversationHistory())

    def handle(self) -> None:
        if not self.generic_handler.setup():
            return
        # setup_main_agent creates an agent, skipping shell state (for one-shot mode)
        self.generic_handler.agent = setup_main_agent(self.args, self.generic_handler.conversation_history)
        print_verbose_header(self.generic_handler.agent, self.args)
        start_time, end_time = self.generic_handler.run_prompt(
            self.args.user_prompt,
            raw=getattr(self.args, 'raw', False)
        )
        print_performance(start_time, end_time, self.generic_handler.performance_collector, self.args)
