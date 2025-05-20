"""
PromptHandler: Handles prompt submission and response formatting for janito CLI (one-shot prompt execution).
"""
import time
from janito.version import __version__ as VERSION
from janito.cli.provider_setup import setup_main_agent
from janito.cli.utils import format_tokens, format_generation_time
from janito.cli.prompt_handler import PromptHandler as GenericPromptHandler
from janito.cli.single_shot_mode.output import print_verbose_header, print_performance, handle_exception
import janito.tools  # Ensure all tools are registered

class PromptHandler:
    def __init__(self, args):
        self.args = args
        from janito.conversation_history import LLMConversationHistory
        # Use setup_main_agent for unified agent initialization
        conversation_history = LLMConversationHistory()
        agent = setup_main_agent(self.args, conversation_history)
        self.generic_handler = GenericPromptHandler(args, conversation_history, provider_instance=agent.driver if agent else None)

    def handle(self) -> None:
        # setup_main_agent creates an agent, skipping shell state (for one-shot mode)
        from janito.cli.provider_setup import setup_main_agent
        self.generic_handler.agent = setup_main_agent(self.args, self.generic_handler.conversation_history)
        print_verbose_header(self.generic_handler.agent, self.args)
        # Ensure user_prompt is a string (CLI passes a list)
        user_prompt = self.args.user_prompt
        if isinstance(user_prompt, list):
            user_prompt = " ".join(user_prompt).strip()
        if not user_prompt or not user_prompt.strip():
            raise ValueError("No user prompt was provided!")
        self.generic_handler.run_prompt(
            user_prompt,
            raw=getattr(self.args, 'raw', False)
        )
        # Performance printing removed with timing
