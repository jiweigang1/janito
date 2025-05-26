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
    GenerationStarted, GenerationFinished, RequestStarted, RequestFinished, RequestError, ResponseReceived
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
    def get_history(self):
        return list(getattr(self, '_history', []))

    def __init__(self, driver_config: LLMDriverConfig, user_prompt: str = None, conversation_history=None, tools_adapter=None):
        if not self.available:
            raise ImportError(f"DashScopeModelDriver unavailable: {self.unavailable_reason}")
        super().__init__(driver_config, user_prompt=user_prompt, conversation_history=conversation_history, tools_adapter=tools_adapter)
        self.config = driver_config

    def _add_to_history(self, message: Dict[str, Any]):
        self._history.append(message)

    def _generate_schemas(self, tools):
        from janito.providers.openai.schema_generator import generate_tool_schemas
        return generate_tool_schemas(tools) if tools else None

    def _process_prompt_and_system(self, messages_or_prompt, system_prompt):
        if isinstance(messages_or_prompt, str):
            user_msg = {"role": "user", "content": messages_or_prompt}
            self._add_to_history(user_msg)
        elif isinstance(messages_or_prompt, list):
            for msg in messages_or_prompt:
                self._add_to_history(dict(msg))
        if system_prompt:
            if not self._history or self._history[0].get('role') != 'system':
                self._history.insert(0, {"role": "system", "content": system_prompt})

    def send_api_request(self, messages, schemas, api_key, enable_thinking=False, **api_kwargs):
        response = Generation.call(
            api_key=api_key,
            model=self.model_name,
            messages=messages,
            tools=schemas,
            result_format="message",
            enable_thinking=enable_thinking,
            **api_kwargs
        )
        return response

    def _run_generation(self, messages_or_prompt: Union[List[Dict[str, Any]], str], system_prompt: Optional[str]=None, tools=None, schemas=None, **kwargs):
        request_id = str(uuid.uuid4())
        self.tools_adapter.event_bus = self.event_bus
        try:
            self._process_prompt_and_system(messages_or_prompt, system_prompt)
            self.publish(GenerationStarted, request_id, conversation_history=self.get_history())
            turn_count = 0
            while True:
                done, response, usage, parts = self._generation_loop_step(tools, kwargs, schemas, self.tools_adapter, request_id, turn_count)
                if done:
                    # Emit ResponseReceived event with all collected parts
                    self.publish(ResponseReceived, request_id=request_id, parts=parts, tool_results=[], timestamp=time.time(), metadata={"raw_response": response, "usage": usage})
                    break
                turn_count += 1
        except Exception as e:
            self.publish(RequestError, request_id, error=str(e), exception=e, traceback=traceback.format_exc())

    def _generation_loop_step(self, tools, kwargs, schemas, tool_executor, request_id, turn_count):
        self.publish(RequestStarted, request_id, payload={"tools": tools})
        enable_thinking = kwargs.get('think', False) or kwargs.get('enable_thinking', False)
        if 'enable_thinking' in kwargs:
            kwargs.pop('enable_thinking')
        messages = self.get_history()
        response = self.send_api_request(messages, schemas, self.api_key, enable_thinking=enable_thinking, **kwargs)
        status_code = getattr(response, 'status_code', None)
        error_code = getattr(response, 'code', None)
        error_message = getattr(response, 'message', None)
        output = getattr(response, 'output', None)
        usage = getattr(response, 'usage', {})

        if status_code is not None and 400 <= status_code < 500:
            self.publish(RequestError, request_id, error=f"{error_code}: {error_message}", exception=None, traceback=None)
            self.publish(GenerationFinished, request_id, total_turns=turn_count+1)
            return True, response, usage, []

        self.publish(RequestFinished, request_id, response=response, status="success", usage=usage)
        if not output or not hasattr(output, 'choices') or not output.choices:
            self.publish(GenerationFinished, request_id, total_turns=turn_count+1)
            return True, response, usage, []
        message = output.choices[0].message
        content = message.get("content") if isinstance(message, dict) else getattr(message, "content", None)
        tool_calls = message.get("tool_calls") if isinstance(message, dict) else getattr(message, "tool_calls", None)
        parts = []
        if content:
            parts.append(TextMessagePart(content=content))
        if tool_calls:
            for tool_call in tool_calls:
                parts.append(FunctionCallMessagePart(
                    tool_call_id=tool_call.get('id', ''),
                    name=tool_call.get('name', ''),
                    arguments=tool_call.get('arguments', {})
                ))
            return False, response, usage, parts
        else:
            self.publish(GenerationFinished, request_id, total_turns=turn_count+1)
            return True, response, usage, parts
