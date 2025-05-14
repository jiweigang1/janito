"""
DashScope LLM driver for Qwen models using the official DashScope Python SDK.
Supports function calling (tool use) via DashScope-compatible API.
Implements multi-turn tool execution (loops until no more tool calls).
"""
import dashscope
from dashscope import Generation
import os
import json
import time
import uuid
import traceback
from typing import Optional
from janito.llm_driver import LLMDriver
from janito.driver_events import (
    GenerationStarted, GenerationFinished, RequestStarted, RequestFinished, RequestError, ContentPartFound
)
from janito.tool_executor import ToolExecutor
from janito.tool_registry import ToolRegistry
from janito.conversation_history import LLMConversationHistory
from janito.providers.openai.schema_generator import generate_tool_schemas

dashscope.base_http_api_url = 'https://dashscope-intl.aliyuncs.com/api/v1'

class DashScopeModelDriver(LLMDriver):
    def _conversation_history_to_driver_messages(self, conversation_history: LLMConversationHistory):
        """
        Convert LLMConversationHistory to DashScope API message format.
        """
        raw_msgs = list(conversation_history.get_history())
        messages = []
        for msg in raw_msgs:
            if msg.get("role") == "tool":
                meta = msg.get("metadata", {})
                messages.append({
                    "role": "tool",
                    "tool_call_id": meta.get("tool_call_id"),
                    "name": meta.get("name"),
                    "content": msg.get("content")
                })
            else:
                messages.append({k: v for k, v in msg.items() if k in ("role", "content")})
        return messages

    def __init__(self, provider_name: str, model_name: str, api_key: str, tool_registry: ToolRegistry = None, think: bool = False):
        super().__init__(provider_name, model_name, api_key, tool_registry)
        self.think = think

    def handle_function_call(self, tool_call, messages, tool_executor):
        func = tool_call.get("function", {})
        tool_name = func.get("name")
        arguments = func.get("arguments")
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except Exception:
                arguments = {}
        result = tool_executor.execute_by_name(tool_name, **(arguments or {}))
        tool_result_msg = {
            "role": "tool",
            "tool_call_id": tool_call.get("id"),
            "name": tool_name,
            "content": str(result)
        }
        messages.append(tool_result_msg)

    def handle_content_part(self, content, request_id):
        self.publish(ContentPartFound, request_id, content_part=content)

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

    def _run_generation(self, conversation_history: LLMConversationHistory, system_prompt: Optional[str]=None, tools=None, **kwargs):
        request_id = str(uuid.uuid4())
        tool_executor = ToolExecutor(registry=self.tool_registry, event_bus=self.event_bus)
        try:
            self.publish(GenerationStarted, request_id, conversation_history=conversation_history)
            schemas = generate_tool_schemas(tools) if tools else None
            messages = self._conversation_history_to_driver_messages(conversation_history)
            turn_count = 0
            start_time = time.time()
            # Inject self.think into kwargs as enable_thinking if not already set
            if 'enable_thinking' not in kwargs and hasattr(self, 'think'):
                kwargs['enable_thinking'] = self.think
            while True:
                self.publish(RequestStarted, request_id, payload={"tools": tools})
                enable_thinking = kwargs.get('think', False) or kwargs.get('enable_thinking', False)
                # Remove enable_thinking from kwargs to avoid duplicate argument
                if 'enable_thinking' in kwargs:
                    kwargs.pop('enable_thinking')
                response = self.send_api_request(messages, schemas, self.api_key, enable_thinking=enable_thinking, **kwargs)
                duration = time.time() - start_time
                output = getattr(response, 'output', None)
                usage = getattr(response, 'usage', {})
                self.publish(RequestFinished, request_id, response=response, duration=duration, status="success", usage=usage)
                if not output or not hasattr(output, 'choices') or not output.choices:
                    self.publish(GenerationFinished, request_id, total_turns=turn_count+1)
                    return
                message = output.choices[0].message
                content = message.get("content") if isinstance(message, dict) else getattr(message, "content", None)
                if content:
                    self.handle_content_part(content, request_id)
                tool_calls = message.get("tool_calls") if isinstance(message, dict) else getattr(message, "tool_calls", None)
                if tool_calls:
                    assistant_msg = {
                        "role": "assistant",
                        "content": content,
                        "tool_calls": tool_calls
                    }
                    messages.append(assistant_msg)
                    for tool_call in tool_calls:
                        self.handle_function_call(tool_call, messages, tool_executor)
                    turn_count += 1
                    continue  # Loop again for multi-turn tool use
                else:
                    self.publish(GenerationFinished, request_id, total_turns=turn_count+1)
                    break
        except Exception as e:
            self.publish(RequestError, request_id, error=str(e), exception=e, traceback=traceback.format_exc())
