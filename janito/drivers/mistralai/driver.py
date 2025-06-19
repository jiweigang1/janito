import time
import uuid
import traceback
import json
from typing import Optional, List, Dict, Any, Union
from janito.llm.driver import LLMDriver
from janito.driver_events import (
    GenerationStarted,
    GenerationFinished,
    RequestStarted,
    RequestFinished,
    ResponseReceived,
)
from janito.providers.openai.schema_generator import generate_tool_schemas
from janito.tools.adapters.local.adapter import LocalToolsAdapter
from janito.llm.message_parts import TextMessagePart, FunctionCallMessagePart
from janito.llm.driver_config import LLMDriverConfig

# Safe import of mistralai SDK
try:
    from mistralai import Mistral

    DRIVER_AVAILABLE = True
    DRIVER_UNAVAILABLE_REASON = None
except ImportError:
    DRIVER_AVAILABLE = False
    DRIVER_UNAVAILABLE_REASON = "Missing dependency: mistralai (pip install mistralai)"


class MistralAIModelDriver(LLMDriver):
    available = False
    unavailable_reason = "MistralAIModelDriver is not implemented yet."

    @classmethod
    def is_available(cls):
        return cls.available

    name = "mistralai"

    def __init__(self, tools_adapter=None):
        raise ImportError(self.unavailable_reason)
