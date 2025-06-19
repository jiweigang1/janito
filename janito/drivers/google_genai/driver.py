"""
Google Gemini LLM driver.

This driver handles interaction with the Google Gemini API, including support for tool/function calls and event publishing.
"""

import json
import time
import uuid
import traceback
from typing import Optional, List, Dict, Any, Union
from janito.llm.driver import LLMDriver
from janito.drivers.google_genai.schema_generator import generate_tool_declarations
from janito.driver_events import (
    GenerationStarted,
    GenerationFinished,
    RequestStarted,
    RequestFinished,
    ResponseReceived,
    RequestStatus,
)
from janito.tools.adapters.local.adapter import LocalToolsAdapter
from janito.llm.message_parts import TextMessagePart, FunctionCallMessagePart
from janito.llm.driver_config import LLMDriverConfig


def extract_usage_metadata_native(usage_obj):
    if usage_obj is None:
        return {}
    result = {}
    for attr in dir(usage_obj):
        if attr.startswith("_") or attr == "__class__":
            continue
        value = getattr(usage_obj, attr)
        if isinstance(value, (str, int, float, bool, type(None))):
            result[attr] = value
        elif isinstance(value, list):
            if all(isinstance(i, (str, int, float, bool, type(None))) for i in value):
                result[attr] = value
    return result


class GoogleGenaiModelDriver(LLMDriver):
    available = False
    unavailable_reason = "GoogleGenaiModelDriver is not implemented yet."

    @classmethod
    def is_available(cls):
        return cls.available

    name = "google_genai"

    def __init__(self, tools_adapter=None):
        raise ImportError(self.unavailable_reason)
