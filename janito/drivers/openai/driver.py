"""
OpenAI LLM driver.

This driver manages interaction with the OpenAI API, supporting both standard chat completions and tool/function calls.

Event Handling:
----------------
When a model response contains both content and tool calls, the driver always publishes the content event (ContentPartFound) first, followed by any tool call events (ToolCallStarted, ToolCallFinished, etc.), regardless of their order in the API response. This is different from the Google Gemini driver, which preserves the original order of parts. This approach ensures that the main content is delivered before any tool execution events for downstream consumers.
"""
import openai
from typing import List, Optional
from janito.llm_driver import LLMDriver
from janito.providers.openai.schema_generator import generate_tool_schemas
import json
import time
from janito.event_bus.bus import event_bus
from janito.driver_events import (
    GenerationStarted, GenerationFinished, RequestStarted, RequestFinished, RequestError, ContentPartFound
)
from janito.utils import kwargs_from_locals

class OpenAIModelDriver(LLMDriver):
    def __init__(self, provider_name: str, model_name: str, api_key: str, tool_executor):
        super().__init__(provider_name, model_name)
        self._api_key = api_key
        self._tool_executor = tool_executor  # ToolExecutor is now required

    def _publish_event(self, event):
        event_bus.publish(event)

    def _handle_tool_calls(self, tool_calls, messages, request_id):
        tool_results = []
        for tool_call in tool_calls:
            func = getattr(tool_call, 'function', None)
            tool_name = getattr(func, 'name', None) if func else None
            arguments = getattr(func, 'arguments', None) if func else None
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except Exception:
                    arguments = {}
            result = self._tool_executor.execute_by_name(tool_name, **(arguments or {}))
            tool_result_msg = {
                "role": "tool",
                "tool_call_id": getattr(tool_call, 'id', None),
                "name": tool_name,
                "content": str(result)
            }
            tool_results.append(tool_result_msg)

        messages.extend(tool_results)
        return tool_results

    def _handle_content(self, content, request_id):
        if content is not None:
            driver_name = self.get_name()
            self._publish_event(ContentPartFound(**kwargs_from_locals('driver_name', 'request_id'), content_part=content))
        return content

    def generate(self, prompt: str, system_prompt: Optional[str] = None, tools=None, **kwargs) -> None:
        import uuid, datetime
        request_id = str(uuid.uuid4())
        driver_name = self.get_name()
        self._publish_event(GenerationStarted(**kwargs_from_locals('driver_name', 'request_id', 'prompt')))
        self._publish_event(RequestStarted(**kwargs_from_locals('driver_name', 'request_id'), payload=prompt))
        if tools:
            schemas = generate_tool_schemas(tools)
            kwargs['tools'] = schemas
        conversation_history = []
        if system_prompt:
            conversation_history.append({"role": "system", "content": system_prompt})
        conversation_history.append({"role": "user", "content": prompt})
        raw = kwargs.pop('raw', False)
        messages = conversation_history[:]
        start_time = time.time()
        try:
            while True:
                response = self._call_openai(None, None, messages=messages, **kwargs)
                duration = time.time() - start_time
                usage_dict = self._extract_usage(response)
                self._publish_event(RequestFinished(**kwargs_from_locals('driver_name', 'request_id', 'response', 'duration'), status='success', usage=usage_dict))
                message = response.choices[0].message
                content = message.content
                self._handle_content(content, request_id)
                tool_calls = getattr(message, 'tool_calls', None)
                if tool_calls:
                    assistant_msg = {
                        "role": "assistant",
                        "content": content,
                        "tool_calls": [tc.to_dict() if hasattr(tc, 'to_dict') else dict(tc.__dict__) for tc in tool_calls]
                    }
                    messages.append(assistant_msg)
                    self._handle_tool_calls(tool_calls, messages, request_id)
                    continue  # Continue the loop for the next model response
                self._publish_event(GenerationFinished(**kwargs_from_locals('driver_name', 'request_id', 'prompt'), total_turns=1))
                return content
        except Exception as e:
            driver_name = self.get_name()
            self._publish_event(RequestError(**kwargs_from_locals('driver_name', 'request_id'), error=str(e), exception=e))
            raise e

    def _call_openai(self, prompt, system_prompt, **kwargs):
        openai.api_key = self._api_key
        client = openai.OpenAI(api_key=self._api_key)
        messages = kwargs.pop('messages', None)
        if messages is None:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
        if (("tools" in kwargs and kwargs['tools']) and 'tool_choice' not in kwargs):
            kwargs['tool_choice'] = 'auto'
        return client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            stream=False,
            **kwargs
        )

    def _extract_usage(self, response):
        usage_obj = getattr(response, 'usage', None)
        usage_dict = {}
        if usage_obj is not None:
            for attr in ('completion_tokens', 'prompt_tokens', 'total_tokens'):
                if hasattr(usage_obj, attr):
                    usage_dict[attr] = getattr(usage_obj, attr)
        return usage_dict
