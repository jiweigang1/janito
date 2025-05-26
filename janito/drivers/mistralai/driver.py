import time
import uuid
import traceback
import json
from typing import Optional, List, Dict, Any, Union
from janito.llm.driver import LLMDriver
from janito.driver_events import (
    GenerationStarted, GenerationFinished, RequestStarted, RequestFinished, RequestError, ResponseReceived
)
from janito.providers.openai.schema_generator import generate_tool_schemas
from janito.tools.adapters.local.adapter import LocalToolsAdapter
from janito.llm.message_parts import TextMessagePart, FunctionCallMessagePart
from janito.llm.driver_config import LLMDriverConfig

# Safe import of mistralai SDK
try:
    from mistralai import Mistral
    DRIVER_AVAILABLE = True
    DRIVER_UNAVAILABLE_REASON = None
except ImportError:
    DRIVER_AVAILABLE = False
    DRIVER_UNAVAILABLE_REASON = "Missing dependency: mistralai (pip install mistralai)"

class MistralAIModelDriver(LLMDriver):
    available = DRIVER_AVAILABLE
    unavailable_reason = DRIVER_UNAVAILABLE_REASON

    @classmethod
    def is_available(cls):
        return cls.available

    name = "mistralai"
    def get_history(self):
        return list(getattr(self, '_history', []))

    def __init__(self, driver_config: LLMDriverConfig, user_prompt: str = None, conversation_history=None, tools_adapter=None):
        if not self.available:
            raise ImportError(f"MistralAIModelDriver unavailable: {self.unavailable_reason}")
        super().__init__(driver_config, user_prompt=user_prompt, conversation_history=conversation_history, tools_adapter=tools_adapter)
        self.config = driver_config
        self._history = []

    def _add_to_history(self, message: dict):
        self._history.append(message)

    def _generate_schemas(self, tools):
        from janito.providers.openai.schema_generator import generate_tool_schemas
        return generate_tool_schemas(tools) if tools else None

    def _process_prompt_and_system(self, messages_or_prompt, system_prompt):
        if isinstance(messages_or_prompt, str):
            self._add_to_history({"role": "user", "content": messages_or_prompt})
        elif isinstance(messages_or_prompt, list):
            for msg in messages_or_prompt:
                self._add_to_history(dict(msg))
        if system_prompt:
            if not self._history or self._history[0].get('role') != 'system':
                self._add_to_history({"role": "system", "content": system_prompt})

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
        tool_calls = getattr(message, 'tool_calls', None)
        parts = []
        if content:
            parts.append(TextMessagePart(content=content))
        had_function_call = False
        if tool_calls:
            for tool_call in tool_calls:
                parts.append(FunctionCallMessagePart(
                    tool_call_id=getattr(tool_call, 'id', ''),
                    name=getattr(getattr(tool_call, 'function', None), 'name', ''),
                    arguments=getattr(getattr(tool_call, 'function', None), 'arguments', {})
                ))
                had_function_call = True
        return had_function_call, duration, response, parts

    def _run_generation(self, messages_or_prompt: Union[List[Dict[str, Any]], str], system_prompt: Optional[str]=None, tools=None, schemas=None, **kwargs):
        request_id = str(uuid.uuid4())
        self.tools_adapter.event_bus = self.event_bus
        try:
            self._process_prompt_and_system(messages_or_prompt, system_prompt)
            self.publish(GenerationStarted, request_id, conversation_history=self._history)
            if not self.available:
                raise ImportError(f"MistralAIModelDriver unavailable: {self.unavailable_reason}")
            client = Mistral(api_key=self.api_key)
            messages = self.get_history()
            turn_count = 0
            start_time = time.time()
            while True:
                if self.cancel_event is not None and self.cancel_event.is_set():
                    self.publish(RequestFinished, request_id, response=None, duration=0, status='cancelled', usage={})
                    self.publish(GenerationFinished, request_id, total_turns=turn_count, status='cancelled')
                    break
                had_function_call, _, response, parts = self._process_generation_turn(
                    client, messages, schemas, tools, request_id, start_time, kwargs, self.tools_adapter
                )
                turn_count += 1
                if had_function_call and (self.cancel_event is None or not self.cancel_event.is_set()):
                    continue
                self.publish(ResponseReceived, request_id=request_id, parts=parts, tool_results=[], timestamp=time.time(), metadata={"raw_response": response})
                self.publish(GenerationFinished, request_id, total_turns=turn_count)
                break
        except Exception as e:
            self.publish(RequestError, request_id, error=str(e), exception=e, traceback=traceback.format_exc())
