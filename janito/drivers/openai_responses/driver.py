"""
OpenAI LLM driver.

This driver manages interaction with the OpenAI API, supporting both standard chat completions and tool/function calls.

Event Handling:
----------------
When a model response contains both content and tool calls, the driver always publishes the content event (ContentPartFound) first, followed by any tool call events, regardless of their order in the API response. This is different from the Google Gemini driver, which preserves the original order of parts. This approach ensures that the main content is delivered before any tool execution events for downstream consumers.
"""
from openai import OpenAI
import json
import time
import uuid
import traceback
from typing import Optional, List, Dict, Any, Union
from janito.llm.driver import LLMDriver
from janito.drivers.openai_responses.schema_generator import generate_tool_schemas
from janito.driver_events import (
    GenerationStarted, GenerationFinished, RequestStarted, RequestFinished, RequestError, ContentPartFound
)
from janito.tools.adapters.local.adapter import LocalToolsAdapter

class OpenAIResponsesModelDriver(LLMDriver):
    name = "openai_responses"
    def get_history(self):
        return list(getattr(self, '_history', []))

    def __init__(self, driver_config, user_prompt: str = None, conversation_history=None, tools_adapter=None):
        super().__init__(driver_config, user_prompt=user_prompt, conversation_history=conversation_history, tools_adapter=tools_adapter)

    def _add_to_history(self, message: Dict[str, Any]):
        self._history.append(message)

    def _handle_function_call(self, tool_call, tool_executor):
        func = getattr(tool_call, 'function', None)
        tool_name = getattr(func, 'name', None) if func else None
        arguments = getattr(func, 'arguments', None) if func else None
        tool_call_id = getattr(tool_call, 'id', None)

        # Explicit checks for required fields
        if not tool_call_id:
            raise ValueError("tool_call.id is missing or None in tool_call: {}".format(tool_call))
        if not tool_name:
            raise ValueError("tool_name is missing or None in tool_call: {}".format(tool_call))

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
            "tool_call_id": tool_call_id,
            "name": tool_name,
            "content": content
        }
        self._add_to_history(tool_result_msg)

    def _handle_content_part(self, content, request_id):
        self.publish(ContentPartFound, request_id, content_part=content)
        assistant_msg = {
            "role": "assistant",
            "content": content
        }
        self._add_to_history(assistant_msg)

    def _send_api_request(self, client, messages, schemas, **api_kwargs):
        # Pass temperature from api_kwargs if present, default to 0
        if schemas:
            api_kwargs['tools'] = schemas
        api_kwargs['model'] = self.model_name
        api_kwargs['input'] = messages
        # Remove any keys not supported by responses API
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

    def _process_tool_calls(self, tool_calls, tool_executor):
        had_function_call = False
        for tool_call in tool_calls:
            if self.cancel_event is not None and self.cancel_event.is_set():
                break
            self._handle_function_call(tool_call, self.tools_adapter)
            had_function_call = True
        return had_function_call

    def _maybe_add_reasoning(self, history_added_indices, output_items, idx):
        if idx > 0:
            prev_item = output_items[idx - 1]
            is_reasoning = (getattr(prev_item, 'type', None) == 'reasoning') or (isinstance(prev_item, dict) and prev_item.get('type') == 'reasoning')
            if is_reasoning and (idx - 1) not in history_added_indices:
                cleaned = {k: v for k, v in (prev_item if isinstance(prev_item, dict) else prev_item.__dict__).items() if k in ('id', 'type', 'summary')}
                self._add_to_history(cleaned)
                history_added_indices.add(idx - 1)

    def _execute_tool_call_and_prepare_result(self, item, tool_executor):
        tool_call = item
        tool_name = getattr(tool_call, 'name', None) if not isinstance(tool_call, dict) else tool_call.get('name')
        arguments = getattr(tool_call, 'arguments', None) if not isinstance(tool_call, dict) else tool_call.get('arguments')
        tool_call_id = getattr(tool_call, 'call_id', None) if not isinstance(tool_call, dict) else tool_call.get('call_id')
        if not tool_call_id:
            tool_call_id = getattr(tool_call, 'id', None) if not isinstance(tool_call, dict) else tool_call.get('id')
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except Exception:
                arguments = {}
        try:
            result = tool_executor.execute_by_name(tool_name, **(arguments or {}))
            tool_content = str(result)
        except Exception as e:
            tool_content = f"Tool execution error: {e}"
        output_msg = {
            "type": "function_call_output",
            "call_id": tool_call_id,
            "output": tool_content
        }
        return output_msg

    def _process_generation_turn(self, client, schemas, tools, request_id, start_time, kwargs, tool_executor):
        api_kwargs = dict(kwargs)
        # Remove non-OpenAI arguments
        api_kwargs.pop('raw', None)
        self.publish(RequestStarted, request_id, payload={
            'tools': tools
        })
        messages = self.get_history()
        response = self._send_api_request(client, messages, schemas, **api_kwargs)
        usage_dict = self._extract_usage(getattr(response, 'usage', None))
        self.publish(RequestFinished, request_id, response=response, status='success', usage=usage_dict)
        content = getattr(response, 'output_text', None)  # OpenAI Responses API v2: main content is in output_text
        if content is not None:
            self._handle_content_part(content, request_id)
        output_items = getattr(response, 'output', None)
        if output_items:
            history_added_indices = set()
            tool_result_msgs = []
            for idx, item in enumerate(output_items):
                is_func_call = (getattr(item, 'type', None) == 'function_call') or (isinstance(item, dict) and item.get('type') == 'function_call')
                if is_func_call:
                    self._maybe_add_reasoning(history_added_indices, output_items, idx)
                    # Now add the function_call itself (CLEANED)
                    func_src = item if isinstance(item, dict) else item.__dict__
                    cleaned_fc = {k: v for k, v in func_src.items() if k in ('id', 'call_id', 'name', 'type', 'arguments')}
                    self._add_to_history(cleaned_fc)
                    history_added_indices.add(idx)
                    tool_result_msgs.append(self._execute_tool_call_and_prepare_result(item, self.tools_adapter))
            for msg in tool_result_msgs:
                self._add_to_history(msg)
            had_function_call = any(
                (getattr(it, 'type', None) == 'function_call' or (isinstance(it, dict) and it.get('type') == 'function_call'))
                for it in output_items
            )
        else:
            had_function_call = False
        return had_function_call, None

    def _run_generation(self, messages_or_prompt: Union[List[Dict[str, Any]], str], system_prompt: Optional[str]=None, tools=None, **kwargs):
        """
        Run a conversation using the provided messages or prompt.
        The driver manages its own internal conversation history.
        """
        request_id = str(uuid.uuid4())
        self.tools_adapter.event_bus = self.event_bus
        try:
            # Do not clear internal history here; accumulate across turns
            if isinstance(messages_or_prompt, str):
                user_msg = {"role": "user", "content": messages_or_prompt}
                self._add_to_history(user_msg)
            elif isinstance(messages_or_prompt, list):
                for msg in messages_or_prompt:
                    self._add_to_history(dict(msg))
            if system_prompt:
                # Ensure system prompt is the first message if provided
                if not self._history or self._history[0].get('role') != 'system':
                    self._history.insert(0, {"role": "system", "content": system_prompt})
            self.publish(GenerationStarted, request_id, conversation_history=self.get_history())
            schemas = generate_tool_schemas(tools) if tools else None
            client = OpenAI(api_key=self.api_key)
            turn_count = 0
            while True:
                if self.cancel_event is not None and self.cancel_event.is_set():
                    self.publish(RequestFinished, request_id, response=None, status='cancelled', usage={})
                    self.publish(GenerationFinished, request_id, total_turns=turn_count, status='cancelled')
                    break
                had_function_call, _ = self._process_generation_turn(
                    client, schemas, tools, request_id, None, kwargs, self.tools_adapter
                )
                turn_count += 1
                if had_function_call and (self.cancel_event is None or not self.cancel_event.is_set()):
                    continue
                self.publish(GenerationFinished, request_id, total_turns=turn_count)
                break
        except Exception as e:
            self.publish(RequestError, request_id, error=str(e), exception=e, traceback=traceback.format_exc())

# Alias for compatibility/dynamic loading
