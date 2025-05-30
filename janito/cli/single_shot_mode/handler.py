"""
PromptHandler: Handles prompt submission and response formatting for janito CLI (one-shot prompt execution).
"""
import time
from janito.version import __version__ as VERSION
from janito.cli.prompt_core import PromptHandler as GenericPromptHandler
from janito.cli.verbose_output import print_verbose_header, print_performance, handle_exception
import janito.tools  # Ensure all tools are registered

class PromptHandler:
    def __init__(self, args, provider_instance, llm_driver_config, role=None):
        self.args = args
        self.provider_instance = provider_instance
        self.llm_driver_config = llm_driver_config
        self.role = role
        from janito.agent.setup_agent import create_configured_agent
        self.agent = create_configured_agent(
    provider_instance=provider_instance,
    llm_driver_config=llm_driver_config,
    role=role,
    verbose_tools=getattr(args, 'verbose_tools', False),
    verbose_agent=getattr(args, 'verbose_agent', False)
)
        # Setup conversation/history if needed
        self.generic_handler = GenericPromptHandler(args, [], provider_instance=provider_instance)
        self.generic_handler.agent = self.agent

    def handle(self) -> None:
        import traceback
        user_prompt = " ".join(getattr(self.args, 'user_prompt', [])).strip()
        try:
            self.generic_handler.handle_prompt(
                user_prompt,
                args=self.args,
                print_header=True,
                raw=getattr(self.args, 'raw', False)
            )
        except Exception as e:
            traceback.print_exc()
