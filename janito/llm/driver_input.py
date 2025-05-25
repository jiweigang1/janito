from dataclasses import dataclass
from typing import Optional, Dict
from janito.llm.driver_config import LLMDriverConfig
from janito.conversation_history import LLMConversationHistory

@dataclass
class DriverInput:
    config: LLMDriverConfig
    conversation_history: LLMConversationHistory
    tool_schema: Optional[Dict] = None
