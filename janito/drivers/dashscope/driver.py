"""
DashScope LLM driver for Qwen models using the official DashScope Python SDK.
Supports function calling (tool use) via DashScope-compatible API.
Implements multi-turn tool execution (loops until no more tool calls).

Main API documentation: https://www.alibabacloud.com/help/en/model-studio/use-qwen-by-calling-api
"""
# Safe import of dashscope SDK
try:
    import dashscope
    from dashscope import Generation
    DRIVER_AVAILABLE = True
    DRIVER_UNAVAILABLE_REASON = None
    dashscope.base_http_api_url = 'https://dashscope-intl.aliyuncs.com/api/v1'
except ImportError:
    DRIVER_AVAILABLE = False
    DRIVER_UNAVAILABLE_REASON = "Missing dependency: dashscope (pip install dashscope)"

import os
import json
import time
import uuid
import traceback
from typing import Optional, List, Dict, Any, Union
from janito.llm.driver import LLMDriver
from janito.driver_events import (
    GenerationStarted, GenerationFinished, RequestStarted, RequestFinished, ResponseReceived
)
from janito.tools.adapters.local.adapter import LocalToolsAdapter
from janito.providers.openai.schema_generator import generate_tool_schemas
from janito.llm.message_parts import TextMessagePart, FunctionCallMessagePart
from janito.llm.driver_config import LLMDriverConfig

class DashScopeModelDriver(LLMDriver):
    available = DRIVER_AVAILABLE
    unavailable_reason = DRIVER_UNAVAILABLE_REASON

    @classmethod
    def is_available(cls):
        return cls.available

    name = "dashscope"

    def __init__(self, tools_adapter=None):
        if not self.available:
            raise ImportError(f"DashScopeModelDriver unavailable: {self.unavailable_reason}")
        super().__init__()
        self.tools_adapter = tools_adapter
        self.config = None
    # ... rest of the implementation ...
