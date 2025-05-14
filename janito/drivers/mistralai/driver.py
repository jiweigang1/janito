"""
MistralAI LLM driver with function calling support.

This driver manages interaction with the MistralAI API, supporting both standard chat completions and function calls.
"""
import time
import uuid
import json
from typing import Optional
from janito.llm_driver import LLMDriver
from janito.driver_events import (
    GenerationStarted, GenerationFinished, RequestStarted, RequestFinished, RequestError, ContentPartFound
)
from janito.providers.openai.schema_generator import generate_tool_schemas
from janito.tool_executor import ToolExecutor
from janito.tool_registry import ToolRegistry

class MistralAIModelDriver(LLMDriver):
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
        try:
            result = tool_executor.execute_by_name(tool_name, **(arguments or {}))
            tool_result_msg = {
                "role": "tool",
                "tool_call_id": getattr(tool_call, 'id', None),
                "name": tool_name,
                "content": str(result)
            }
            messages.append(tool_result_msg)
        except Exception:
            pass

    def handle_content_part(self, content, request_id):
        self.publish(ContentPartFound, request_id, content_part=content)

    def send_api_request(self, client, messages, schemas, **api_kwargs):
        if schemas:
            api_kwargs['tools'] = schemas
            if 'tool_choice' not in api_kwargs:
                api_kwargs['tool_choice'] = 'auto'
        api_kwargs['model'] = self.model_name
        api_kwargs['messages'] = messages
        return client.chat.complete(**api_kwargs)

    def _process_generation_turn(self, client, messages, schemas, prompt, system_prompt, tools, request_id, start_time, kwargs, tool_executor):
        api_kwargs = dict(kwargs)
        self.publish(RequestStarted, request_id, payload={
            'prompt': prompt,
            'system_prompt': system_prompt,
            'tools': tools
        })
        response = self.send_api_request(client, messages, schemas, **api_kwargs)
        duration = time.time() - start_time
        self.publish(RequestFinished, request_id, response=response, duration=duration, status='success', usage={})
        message = response.choices[0].message
        content = message.content
        if content:
            self.handle_content_part(content, request_id)
        tool_calls = getattr(message, 'tool_calls', None)
        had_function_call = False
        if tool_calls:
            assistant_msg = {
                "role": "assistant",
                "content": content,
                "tool_calls": [tc.to_dict() if hasattr(tc, 'to_dict') else dict(tc.__dict__) for tc in tool_calls]
            }
            messages.append(assistant_msg)
            for tool_call in tool_calls:
                if self.cancel_event is not None and self.cancel_event.is_set():
                    break
                self.handle_function_call(tool_call, messages, tool_executor)
                had_function_call = True
        return had_function_call, duration

    def _run_generation(self, prompt: str, system_prompt: Optional[str], tools=None, **kwargs):
        request_id = str(uuid.uuid4())
        tool_executor = ToolExecutor(registry=self.tool_registry, event_bus=self.event_bus)
        try:
            self.publish(GenerationStarted, request_id, prompt=prompt)
            from mistralai import Mistral
            client = Mistral(api_key=self.api_key)
            schemas = generate_tool_schemas(tools) if tools else None
            conversation_history = []
            if system_prompt:
                conversation_history.append({"role": "system", "content": system_prompt})
            conversation_history.append({"role": "user", "content": prompt})
            messages = conversation_history[:]
            max_retries = 5
            backoff_base = 1.0
            attempt = 0
            turn_count = 0
            start_time = time.time()
            while True:
                if self.cancel_event is not None and self.cancel_event.is_set():
                    self.publish(RequestFinished, request_id, response=None, duration=0, status='cancelled', usage={})
                    self.publish(GenerationFinished, request_id, total_turns=turn_count, status='cancelled')
                    break
                # Retry logic for 429 errors
                while attempt <= max_retries:
                    try:
                        had_function_call, _ = self._process_generation_turn(
                            client, messages, schemas, prompt, system_prompt, tools, request_id, start_time, kwargs, tool_executor
                        )
                        break
                    except Exception as e:
                        error_str = str(e)
                        if (
                            'Status 429' in error_str and
                            'Service tier capacity exceeded for this model' in error_str
                        ):
                            self.publish(RequestError, request_id, error=error_str, exception=e)
                            if attempt == max_retries:
                                return
                            sleep_time = backoff_base * (2 ** attempt)
                            time.sleep(sleep_time)
                            attempt += 1
                            continue
                        else:
                            self.publish(RequestError, request_id, error=str(e), exception=e)
                            return
                else:
                    return
                turn_count += 1
                if had_function_call and (self.cancel_event is None or not self.cancel_event.is_set()):
                    continue
                self.publish(GenerationFinished, request_id, total_turns=turn_count)
                break
        except Exception as e:
            self.publish(RequestError, request_id, error=str(e), exception=e)
