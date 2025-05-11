import openai
from typing import List, Optional
from janito.llm_driver import LLMDriver
from janito.providers.openai.schema_generator import generate_tool_schemas
import json
import time
from janito.event_bus.bus import event_bus
from janito.event_types import (
    
    GenerationStarted, GenerationFinished, RequestStarted, RequestFinished, ResponseReceived, RequestError, ToolCallStarted, ToolCallFinished, ContentPartFound
)

class OpenAIModelDriver(LLMDriver):
    def __init__(self, provider_name: str, model_name: str, api_key: str, tool_executor):
        super().__init__(provider_name, model_name)
        self._api_key = api_key
        self._tool_executor = tool_executor  # ToolExecutor is now required

    def generate(self, prompt: str, system_prompt: Optional[str] = None, tools=None, **kwargs):
        import uuid, datetime
        request_id = str(uuid.uuid4())
        import datetime
        event_bus.publish(GenerationStarted(self.get_name(), request_id, prompt))
        event_bus.publish(RequestStarted(self.get_name(), request_id, prompt))
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
                event_bus.publish(RequestFinished(self.get_name(), request_id, response, duration, 'success'))
                event_bus.publish(ResponseReceived(self.get_name(), request_id, response))
                message = response.choices[0].message
                content = message.content
                if content is not None:
                    event_bus.publish(ContentPartFound(self.get_name(), request_id, content))
                tool_calls = getattr(message, 'tool_calls', None)
                usage_dict = self._extract_usage(response)
                if tool_calls:
                    assistant_msg = {
                        "role": "assistant",
                        "content": content,
                        "tool_calls": [tc.to_dict() if hasattr(tc, 'to_dict') else dict(tc.__dict__) for tc in tool_calls]
                    }
                    messages.append(assistant_msg)
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
                        event_bus.publish(ToolCallStarted(tool_name, request_id, arguments))
                        try:
                            result = self._tool_executor.execute_by_name(tool_name, **(arguments or {}))
                            tool_result_msg = {
                                "role": "tool",
                                "tool_call_id": getattr(tool_call, 'id', None),
                                "name": tool_name,
                                "content": str(result)
                            }
                            tool_results.append(tool_result_msg)
                            event_bus.publish(ToolCallFinished(tool_name, request_id, result))
                        except Exception as e:
                            error_msg = {
                                "role": "tool",
                                "tool_call_id": getattr(tool_call, 'id', None),
                                "name": tool_name,
                                "content": f"Tool execution error: {str(e)}"
                            }
                            tool_results.append(error_msg)
                            event_bus.publish(RequestError(self.get_name(), request_id, str(e), e))
                    messages.extend(tool_results)
                    continue  # Continue the loop for the next model response
                event_bus.publish(GenerationFinished(self.get_name(), request_id, prompt, 1))
                return content
        except Exception as e:
            event_bus.publish(RequestError(self.get_name(), request_id, str(e), e))
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
