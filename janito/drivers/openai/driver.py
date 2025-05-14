"""
OpenAI LLM driver.

This driver manages interaction with the OpenAI API, supporting both standard chat completions and tool/function calls.

Event Handling:
----------------
When a model response contains both content and tool calls, the driver always publishes the content event (ContentPartFound) first, followed by any tool call events, regardless of their order in the API response. This is different from the Google Gemini driver, which preserves the original order of parts. This approach ensures that the main content is delivered before any tool execution events for downstream consumers.
"""
import openai
import json
import time
import uuid
import traceback
from typing import Optional
from janito.llm_driver import LLMDriver
from janito.providers.openai.schema_generator import generate_tool_schemas
from janito.driver_events import (
    GenerationStarted, GenerationFinished, RequestStarted, RequestFinished, RequestError, ContentPartFound
)
from janito.tool_executor import ToolExecutor
from janito.tool_registry import ToolRegistry
from janito.conversation_history import LLMConversationHistory

class OpenAIModelDriver(LLMDriver):
    def _conversation_history_to_driver_messages(self, conversation_history: LLMConversationHistory):
        """
        Convert LLMConversationHistory to OpenAI API message format.
        """
        raw_msgs = list(conversation_history.get_history())
        messages = []
        for msg in raw_msgs:
            if msg.get("role") == "tool":
                meta = msg.get("metadata", {})
                # Tool call (arguments present, content is None)
                if meta.get("arguments") is not None and msg.get("content") is None:
                    messages.append({
                        "role": "tool",
                        "tool_call_id": meta.get("tool_call_id"),
                        "name": meta.get("name"),
                        "content": None,  # OpenAI expects content for tool responses only
                        "arguments": meta.get("arguments")
                    })
                # Tool response (content present)
                elif msg.get("content") is not None:
                    messages.append({
                        "role": "tool",
                        "tool_call_id": meta.get("tool_call_id"),
                        "name": meta.get("name"),
                        "content": msg.get("content")
                    })
            else:
                # user, assistant, system
                messages.append({k: v for k, v in msg.items() if k in ("role", "content")})
        return messages

    def __init__(self, provider_name: str, model_name: str, api_key: str, tool_registry: ToolRegistry = None):
        super().__init__(provider_name, model_name, api_key, tool_registry)

    def handle_function_call(self, tool_call, messages, tool_executor):
        func = getattr(tool_call, 'function', None)
        tool_name = getattr(func, 'name', None) if func else None
        arguments = getattr(func, 'arguments', None) if func else None
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except Exception:
                arguments = {}
        result = tool_executor.execute_by_name(tool_name, **(arguments or {}))
        tool_result_msg = {
            "role": "tool",
            "tool_call_id": getattr(tool_call, 'id', None),
            "name": tool_name,
            "content": str(result)
        }
        messages.append(tool_result_msg)

    def handle_content_part(self, content, request_id):
        self.publish(ContentPartFound, request_id, content_part=content)

    def send_api_request(self, client, messages, schemas, **api_kwargs):
        if schemas:
            api_kwargs['tools'] = schemas
            if 'tool_choice' not in api_kwargs:
                api_kwargs['tool_choice'] = 'auto'
        api_kwargs['model'] = self.model_name
        api_kwargs['messages'] = messages
        api_kwargs['stream'] = False
        return client.chat.completions.create(**api_kwargs)

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

    def _process_tool_calls(self, tool_calls, messages, tool_executor):
        had_function_call = False
        for tool_call in tool_calls:
            if self.cancel_event is not None and self.cancel_event.is_set():
                break
            self.handle_function_call(tool_call, messages, tool_executor)
            had_function_call = True
        return had_function_call

    def _process_generation_turn(self, client, messages, schemas, tools, request_id, start_time, kwargs, tool_executor):
        api_kwargs = dict(kwargs)
        self.publish(RequestStarted, request_id, payload={
            'tools': tools
        })
        response = self.send_api_request(client, messages, schemas, **api_kwargs)
        duration = time.time() - start_time
        usage_dict = self._extract_usage(getattr(response, 'usage', None))
        self.publish(RequestFinished, request_id, response=response, duration=duration, status='success', usage=usage_dict)
        message = response.choices[0].message
        content = message.content
        if content is not None:
            self.handle_content_part(content, request_id)
        tool_calls = getattr(message, 'tool_calls', None)
        if tool_calls:
            assistant_msg = {
                "role": "assistant",
                "content": content,
                "tool_calls": [tc.to_dict() if hasattr(tc, 'to_dict') else dict(tc.__dict__) for tc in tool_calls]
            }
            messages.append(assistant_msg)
            had_function_call = self._process_tool_calls(tool_calls, messages, tool_executor)
        else:
            had_function_call = False
        return had_function_call, duration

    def _run_generation(self, conversation_history: LLMConversationHistory, system_prompt: Optional[str]=None, tools=None, **kwargs):
        """
        Run a conversation using the provided conversation history (LLMConversationHistory).
        The driver will not mutate the original conversation history.
        """
        request_id = str(uuid.uuid4())
        tool_executor = ToolExecutor(registry=self.tool_registry, event_bus=self.event_bus)
        try:
            self.publish(GenerationStarted, request_id, conversation_history=conversation_history)
            schemas = generate_tool_schemas(tools) if tools else None
            messages = self._conversation_history_to_driver_messages(conversation_history)

            client = openai.OpenAI(api_key=self.api_key)
            turn_count = 0
            start_time = time.time()
            while True:
                if self.cancel_event is not None and self.cancel_event.is_set():
                    self.publish(RequestFinished, request_id, response=None, duration=0, status='cancelled', usage={})
                    self.publish(GenerationFinished, request_id, total_turns=turn_count, status='cancelled')
                    break
                had_function_call, _ = self._process_generation_turn(
                    client, messages, schemas, tools, request_id, start_time, kwargs, tool_executor
                )
                turn_count += 1
                if had_function_call and (self.cancel_event is None or not self.cancel_event.is_set()):
                    continue
                self.publish(GenerationFinished, request_id, total_turns=turn_count)
                break
        except Exception as e:
            self.publish(RequestError, request_id, error=str(e), exception=e, traceback=traceback.format_exc())
