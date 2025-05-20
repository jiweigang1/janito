from janito.llm.agent import LLMAgent
from typing import Optional, Any

class MainAgent(LLMAgent):
    def __init__(self, driver, provider=None, agent_name: Optional[str] = None, system_prompt: Optional[str] = None, tools: Optional[list] = None, temperature: Optional[float] = None, **kwargs: Any):
        super().__init__(driver, agent_name, system_prompt, tools, temperature, **kwargs)
        self.provider = provider
        self._role = None
        self._runtime_info = {}

    def set_role(self, role: str):
        self._role = role

    def get_role(self) -> Optional[str]:
        return self._role

    def set_runtime_info(self, **runtime_info):
        self._runtime_info.update(runtime_info)

    def get_runtime_info(self) -> dict:
        return self._runtime_info
