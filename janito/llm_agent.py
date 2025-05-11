from janito.llm_driver import LLMDriver
from janito.conversation_history import LLMConversationHistory
from janito.tool_registry import ToolRegistry
from typing import Any, Optional, List

class LLMAgent:
    """
    Represents an agent that interacts with an LLM driver to generate responses and manage conversation state.
    The agent's performance data (execution time, token usage, etc.) can be accessed via the get_performance_data() method or performance property.
    """
    def __init__(self, driver: LLMDriver, agent_name: Optional[str] = None, history: Optional[LLMConversationHistory] = None, system_prompt: Optional[str] = None, tools: Optional[List[dict]] = None, **kwargs: Any):
        self.driver = driver
        self.agent_name = agent_name or driver.get_name()
        self.state = {}
        self.config = kwargs
        self.history = history if history is not None else LLMConversationHistory()
        self.system_prompt = system_prompt
        if self.system_prompt:
            history_messages = self.history.get_history()
            if not history_messages or history_messages[0].get('role') != 'system':
                self.history.add_message('system', self.system_prompt)
        if tools is None:
            self.tools = ToolRegistry().get_tool_classes()
        else:
            self.tools = tools

    def set_system_prompt(self, prompt: str) -> None:
        self.system_prompt = prompt

    def get_system_prompt(self) -> Optional[str]:
        return self.system_prompt

    def chat(self, prompt: str, role: str = "user", **kwargs: Any) -> str:
        self.history.add_message(role, prompt)
        generate_kwargs = dict(
            prompt=prompt,
            system_prompt=self.system_prompt,
            **kwargs
        )
        if self.tools:
            generate_kwargs['tools'] = self.tools
        response = self.driver.generate(**generate_kwargs)
        if response is not None:
            self.history.add_message("assistant", response)
        return response

    def get_name(self) -> str:
        return self.agent_name
