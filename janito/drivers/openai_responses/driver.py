"""
OpenAI LLM driver.

This driver manages interaction with the OpenAI API, supporting both standard chat completions and tool/function calls.
"""
# Safe import of openai SDK
try:
    from openai import OpenAI
    DRIVER_AVAILABLE = True
    DRIVER_UNAVAILABLE_REASON = None
except ImportError:
    DRIVER_AVAILABLE = False
    DRIVER_UNAVAILABLE_REASON = "Missing dependency: openai (pip install openai)"
import json
import time
import uuid
import traceback
from typing import Optional, List, Dict, Any, Union
from janito.llm.driver import LLMDriver
from janito.drivers.openai_responses.schema_generator import generate_tool_schemas
from janito.driver_events import (
    GenerationStarted, GenerationFinished, RequestStarted, RequestFinished, RequestError, ResponseReceived
)
from janito.tools.adapters.local.adapter import LocalToolsAdapter
from janito.llm.message_parts import TextMessagePart, FunctionCallMessagePart

class OpenAIResponsesModelDriver(LLMDriver):
    available = DRIVER_AVAILABLE
    unavailable_reason = DRIVER_UNAVAILABLE_REASON

    @classmethod
    def is_available(cls):
        return cls.available

    name = "openai_responses"
    def get_history(self):
        return list(getattr(self, '_history', []))

    def __init__(self, driver_config, user_prompt: str = None, conversation_history=None, tools_adapter=None):
        if not self.available:
            raise ImportError(f"OpenAIResponsesModelDriver unavailable: {self.unavailable_reason}")
        super().__init__(driver_config, user_prompt=user_prompt, conversation_history=conversation_history, tools_adapter=tools_adapter)

    def _add_to_history(self, message: Dict[str, Any]):
        self._history.append(message)

    def _generate_schemas(self, tools):
        from janito.drivers.openai_responses.schema_generator import generate_tool_schemas
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

    def _send_api_request(self, client, messages, schemas, **api_kwargs):
        if schemas:
            api_kwargs['tools'] = schemas
        api_kwargs['model'] = self.model_name
        api_kwargs['input'] = messages
        api_kwargs.pop('messages', None)
        api_kwargs.pop('stream', None)
        api_kwargs.pop('tool_choice', None)
        return client.responses.create(**api_kwargs)

    def _extract_usage(self, usage):
        usage_dict = {}
        if usage:
            for attr in dir(usage):
                if attr.startswith('_') or attr == '__class__':
                    continue
                value = getattr(usage, attr)
                if isinstance(value, (str, int, float, bool, type(None))):
                    usage_dict[attr] = value
                elif isinstance(value, list):
                    if all(isinstance(i, (str, int, float, bool, type(None))) for i in value):
                        usage_dict[attr] = value
        return usage_dict

    def _run_generation(self, messages_or_prompt: Union[List[Dict[str, Any]], str], system_prompt: Optional[str]=None, tools=None, **kwargs):
        request_id = str(uuid.uuid4())
        self.tools_adapter.event_bus = self.event_bus
        try:
            if isinstance(messages_or_prompt, str):
                user_msg = {"role": "user", "content": messages_or_prompt}
                self._add_to_history(user_msg)
            elif isinstance(messages_or_prompt, list):
                for msg in messages_or_prompt:
                    self._add_to_history(dict(msg))
            if system_prompt:
                if not self._history or self._history[0].get('role') != 'system':
                    self._history.insert(0, {"role": "system", "content": system_prompt})
            self.publish(GenerationStarted, request_id, conversation_history=self.get_history())
            schemas = generate_tool_schemas(tools) if tools else None
            client = OpenAI(api_key=self.api_key)
            turn_count = 0
            start_time = time.time()
            while True:
                if self.cancel_event is not None and self.cancel_event.is_set():
                    self.publish(RequestFinished, request_id, response=None, status='cancelled', usage={})
                    self.publish(GenerationFinished, request_id, total_turns=turn_count, status='cancelled')
                    break
                done, response, usage_dict, parts = self._process_generation_turn(
                    client, schemas, tools, request_id, start_time, kwargs
                )
                turn_count += 1
                if done:
                    self.publish(ResponseReceived, request_id=request_id, parts=parts, tool_results=[], timestamp=time.time(), metadata={"raw_response": response, "usage": usage_dict})
                    self.publish(GenerationFinished, request_id, total_turns=turn_count)
                    break
        except Exception as e:
            self.publish(RequestError, request_id, error=str(e), exception=e, traceback=traceback.format_exc())

    def _process_generation_turn(self, client, schemas, tools, request_id, start_time, kwargs):
        api_kwargs = dict(kwargs)
        api_kwargs.pop('raw', None)
        self.publish(RequestStarted, request_id, payload={
            'tools': tools
        })
        messages = self.get_history()
        response = self._send_api_request(client, messages, schemas, **api_kwargs)
        usage_dict = self._extract_usage(getattr(response, 'usage', None))
        self.publish(RequestFinished, request_id, response=response, status='success', usage=usage_dict)
        content = getattr(response, 'output_text', None)
        output_items = getattr(response, 'output', None)
        parts = []
        if content is not None:
            parts.append(TextMessagePart(content=content))
        if output_items:
            for item in output_items:
                is_func_call = (getattr(item, 'type', None) == 'function_call') or (isinstance(item, dict) and item.get('type') == 'function_call')
                if is_func_call:
                    func_src = item if isinstance(item, dict) else item.__dict__
                    parts.append(FunctionCallMessagePart(
                        tool_call_id=func_src.get('id', '') or func_src.get('call_id', ''),
                        name=func_src.get('name', ''),
                        arguments=func_src.get('arguments', {})
                    ))
        return True, response, usage_dict, parts
