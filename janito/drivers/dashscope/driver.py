"""
DashScope LLM driver for Qwen models using the official DashScope Python SDK.
Supports function calling (tool use) via DashScope-compatible API.
Implements multi-turn tool execution (loops until no more tool calls).

Main API documentation: https://www.alibabacloud.com/help/en/model-studio/use-qwen-by-calling-api
"""
import dashscope
from dashscope import Generation
import os
import json
import time
import uuid
import traceback
from typing import Optional, List, Dict, Any, Union
from janito.llm.driver import LLMDriver
from janito.driver_events import (
    GenerationStarted, GenerationFinished, RequestStarted, RequestFinished, RequestError, ContentPartFound
)
from janito.tool_executor import ToolExecutor
from janito.tool_registry import ToolRegistry
from janito.providers.openai.schema_generator import generate_tool_schemas

from janito.llm.driver_config import LLMDriverConfig

dashscope.base_http_api_url = 'https://dashscope-intl.aliyuncs.com/api/v1'

class DashScopeModelDriver(LLMDriver):
    name = "dashscope"
    def get_history(self):
        return list(getattr(self, '_history', []))

    def __init__(self, info: LLMDriverConfig, tool_registry: ToolRegistry = None):
        super().__init__('dashscope', info.model, info.api_key, tool_registry)
        self.config = info

    def _add_to_history(self, message: Dict[str, Any]):
        self._history.append(message)

    def handle_function_call(self, tool_call, tool_executor):
        func = tool_call.get("function", {})
        tool_name = func.get("name")
        arguments = func.get("arguments")
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except Exception:
                arguments = {}
        try:
            result = tool_executor.execute_by_name(tool_name, **(arguments or {}))
            content = str(result)
        except Exception as e:
            content = f"Tool execution error: {e}"
        tool_result_msg = {
            "role": "tool",
            "tool_call_id": tool_call.get("id"),
            "name": tool_name,
            "content": content
        }
        self._add_to_history(tool_result_msg)

    def handle_content_part(self, content, request_id):
        self.publish(ContentPartFound, request_id, content_part=content)
        assistant_msg = {
            "role": "assistant",
            "content": content
        }
        self._add_to_history(assistant_msg)

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

    def _run_generation(self, messages_or_prompt: Union[List[Dict[str, Any]], str], system_prompt: Optional[str]=None, tools=None, **kwargs):
        request_id = str(uuid.uuid4())
        tool_executor = ToolExecutor(registry=self.tool_registry, event_bus=self.event_bus)
        try:
            self._process_prompt_and_system(messages_or_prompt, system_prompt)
            self.publish(GenerationStarted, request_id, conversation_history=self.get_history())
            schemas = generate_tool_schemas(tools) if tools else None
            turn_count = 0
            while True:
                done = self._generation_loop_step(tools, kwargs, schemas, tool_executor, request_id, turn_count)
                if done:
                    break
                turn_count += 1
        except Exception as e:
            self.publish(RequestError, request_id, error=str(e), exception=e, traceback=traceback.format_exc())

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

        # Handle client errors
        if status_code is not None and 400 <= status_code < 500:
            self.publish(RequestError, request_id, error=f"{error_code}: {error_message}", exception=None, traceback=None)
            self.publish(GenerationFinished, request_id, total_turns=turn_count+1)
            return True

        self.publish(RequestFinished, request_id, response=response, status="success", usage=usage)
        if not output or not hasattr(output, 'choices') or not output.choices:
            self.publish(GenerationFinished, request_id, total_turns=turn_count+1)
            return True
        message = output.choices[0].message
        content = message.get("content") if isinstance(message, dict) else getattr(message, "content", None)
        if content:
            self.handle_content_part(content, request_id)
        tool_calls = message.get("tool_calls") if isinstance(message, dict) else getattr(message, "tool_calls", None)
        if tool_calls:
            # Prepare the assistant message and add to history
            assistant_msg = {
                "role": "assistant",
                "content": content,
                "tool_calls": [tc.to_dict() if hasattr(tc, 'to_dict') else dict(tc) for tc in tool_calls]
            }
            self._add_to_history(assistant_msg)
            for tool_call in tool_calls:
                self.handle_function_call(tool_call, tool_executor)
            return False  # Not done
        else:
            self.publish(GenerationFinished, request_id, total_turns=turn_count+1)
            return True
