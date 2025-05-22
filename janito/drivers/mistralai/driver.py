import time
import uuid
import traceback
import json
from typing import Optional, List, Dict, Any, Union
from janito.llm.driver import LLMDriver
from janito.driver_events import (
    GenerationStarted, GenerationFinished, RequestStarted, RequestFinished, RequestError, ContentPartFound
)
from janito.providers.openai.schema_generator import generate_tool_schemas
from janito.tool_executor import ToolExecutor
from janito.tool_registry import ToolRegistry

from janito.llm.driver_config import LLMDriverConfig

class MistralAIModelDriver(LLMDriver):
    name = "mistralai"
    def get_history(self):
        return list(getattr(self, '_history', []))

    def __init__(self, driver_config: LLMDriverConfig, tool_registry: ToolRegistry = None):
        super().__init__('mistralai', driver_config.model, driver_config.api_key, tool_registry)
        self.config = driver_config
        self._history = []

    def _add_to_history(self, message: dict):
        self._history.append(message)

    def handle_function_call(self, tool_call, tool_executor):
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
            content = str(result)
        except Exception as e:
            content = f"Tool execution error: {e}"
        tool_result_msg = {
            "role": "tool",
            "tool_call_id": getattr(tool_call, 'id', None),
            "name": tool_name,
            "content": content
        }
        self._add_to_history(tool_result_msg)

    def handle_content_part(self, content, request_id):
        self.publish(ContentPartFound, request_id, content_part=content)
        self._add_to_history({"role": "assistant", "content": content})

    def send_api_request(self, client, messages, schemas, **api_kwargs):
        if schemas:
            api_kwargs['tools'] = schemas
            if 'tool_choice' not in api_kwargs:
                api_kwargs['tool_choice'] = 'auto'
        api_kwargs['model'] = self.model_name
        api_kwargs['messages'] = messages
        return client.chat.complete(**api_kwargs)

    def _process_generation_turn(self, client, messages, schemas, tools, request_id, start_time, kwargs, tool_executor):
        api_kwargs = dict(kwargs)
        self.publish(RequestStarted, request_id, payload={
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
            # Prepare the assistant message but do not add to history yet
            assistant_msg = {
                "role": "assistant",
                "content": content,
                "tool_calls": [tc.to_dict() if hasattr(tc, 'to_dict') else dict(tc.__dict__) for tc in tool_calls]
            }
            # Execute tool(s) and collect result messages
            for tool_call in tool_calls:
                if self.cancel_event is not None and self.cancel_event.is_set():
                    break
                self.handle_function_call(tool_call, tool_executor)
                had_function_call = True
            # Now add the assistant message to history after all tool results are available
            self._add_to_history(assistant_msg)
        return had_function_call, duration

    def _run_generation(self, messages_or_prompt: Union[List[Dict[str, Any]], str], system_prompt: Optional[str]=None, tools=None, **kwargs):
        request_id = str(uuid.uuid4())
        tool_executor = ToolExecutor(registry=self.tool_registry, event_bus=self.event_bus)
        try:
            self._process_prompt_and_system(messages_or_prompt, system_prompt)
            self.publish(GenerationStarted, request_id, conversation_history=self._history)
            from mistralai import Mistral
            client = Mistral(api_key=self.api_key)
            schemas = generate_tool_schemas(tools) if tools else None
            self._generation_turn_loop(client, schemas, tools, request_id, kwargs, tool_executor)
        except Exception as e:
            self.publish(RequestError, request_id, error=str(e), exception=e, traceback=traceback.format_exc())

    def _process_prompt_and_system(self, messages_or_prompt, system_prompt):
        if isinstance(messages_or_prompt, str):
            self._add_to_history({"role": "user", "content": messages_or_prompt})
        elif isinstance(messages_or_prompt, list):
            for msg in messages_or_prompt:
                self._add_to_history(dict(msg))
        if system_prompt:
            if not self._history or self._history[0].get('role') != 'system':
                self._add_to_history({"role": "system", "content": system_prompt})

    def _generation_turn_loop(self, client, schemas, tools, request_id, kwargs, tool_executor):
        messages = []
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
                        client, messages, schemas, tools, request_id, start_time, kwargs, tool_executor
                    )
                    break
                except Exception as e:
                    error_str = str(e)
                    if (
                        'Status 429' in error_str and
                        'Service tier capacity exceeded for this model' in error_str
                    ):
                        self.publish(RequestError, request_id, error=error_str, exception=e, traceback=traceback.format_exc())
                        if attempt == max_retries:
                            return
                        sleep_time = backoff_base * (2 ** attempt)
                        time.sleep(sleep_time)
                        attempt += 1
                        continue
                    else:
                        self.publish(RequestError, request_id, error=str(e), exception=e, traceback=traceback.format_exc())
                        return
            else:
                return
            turn_count += 1
            if had_function_call and (self.cancel_event is None or not self.cancel_event.is_set()):
                continue
            self.publish(GenerationFinished, request_id, total_turns=turn_count)
            break
