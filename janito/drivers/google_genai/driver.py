"""
Google Gemini LLM driver.

This driver handles interaction with the Google Gemini API, including support for tool/function calls and event publishing.
"""
import json
import time
import uuid
import traceback
from typing import Optional, List, Dict, Any, Union
from janito.llm.driver import LLMDriver
from janito.drivers.google_genai.schema_generator import generate_tool_declarations
from janito.driver_events import (
    GenerationStarted, GenerationFinished, RequestStarted, RequestFinished, RequestError, ResponseReceived, EmptyResponseEvent
)
from janito.tools.adapters.local.adapter import LocalToolsAdapter
from janito.llm.message_parts import TextMessagePart, FunctionCallMessagePart
from janito.llm.driver_config import LLMDriverConfig

def extract_usage_metadata_native(usage_obj):
    if usage_obj is None:
        return {}
    result = {}
    for attr in dir(usage_obj):
        if attr.startswith("_") or attr == "__class__":
            continue
        value = getattr(usage_obj, attr)
        if isinstance(value, (str, int, float, bool, type(None))):
            result[attr] = value
        elif isinstance(value, list):
            if all(isinstance(i, (str, int, float, bool, type(None))) for i in value):
                result[attr] = value
    return result

class GoogleGenaiModelDriver(LLMDriver):
    available = True
    unavailable_reason = None

    @classmethod
    def is_available(cls):
        return cls.available

    name = "google_genai"
    def __init__(self, driver_config: LLMDriverConfig, user_prompt: str = None, conversation_history=None, tools_adapter=None):
        if not self.available:
            raise ImportError(f"GoogleGenaiModelDriver unavailable: {self.unavailable_reason}")
        super().__init__(driver_config, user_prompt=user_prompt, conversation_history=conversation_history, tools_adapter=tools_adapter)
        self.config = driver_config
        self._history: List[Dict[str, Any]] = []

    def _add_to_history(self, message: Dict[str, Any]):
        self._history.append(message)

    def get_history(self):
        return list(self._history)

    def _conversation_history_to_driver_messages(self, history_msgs: List[Dict[str, Any]]):
        from google.genai import types as genai_types_local
        msgs = list(history_msgs)
        system_prompt = None
        if msgs and isinstance(msgs[0], dict) and msgs[0].get('role') == 'system':
            system_prompt = msgs.pop(0).get('content')
        conversation_contents = []
        for msg in msgs:
            if msg.get("role") == "tool":
                meta = msg.get("metadata", {})
                if meta.get("arguments") is not None and msg.get("content") is None:
                    conversation_contents.append(
                        genai_types_local.Content(
                            role="user",
                            parts=[genai_types_local.Part(function_call={
                                "name": meta.get("name"),
                                "args": meta.get("arguments")
                            })]
                        )
                    )
                elif msg.get("content") is not None:
                    conversation_contents.append(
                        genai_types_local.Content(
                            role="tool",
                            parts=[genai_types_local.Part(
                                function_response={
                                    "name": meta.get("name"),
                                    "response": {"result": msg.get("content")}
                                }
                            )]
                        )
                    )
            else:
                conversation_contents.append(
                    genai_types_local.Content(
                        role=msg.get("role"),
                        parts=[genai_types_local.Part(text=msg.get("content"))]
                    )
                )
        return conversation_contents, system_prompt

    def _generate_schemas(self, tools):
        from janito.drivers.google_genai.schema_generator import generate_tool_declarations
        return generate_tool_declarations(tools) if tools else None

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

    def send_api_request(self, client, conversation_contents, **api_kwargs):
        return client.models.generate_content(
            model=self.model_name,
            contents=conversation_contents,
            **api_kwargs
        )

    def _process_generation_turn(self, client, config, conversation_contents, tool_executor, tools, request_id, start_time, kwargs):
        api_kwargs = dict(kwargs)
        if config:
            api_kwargs['config'] = config
        self.publish(RequestStarted, request_id, payload={
            'tools': tools
        })
        response = self.send_api_request(client, conversation_contents, **api_kwargs)
        duration = time.time() - start_time
        usage_obj = getattr(response, 'usage_metadata', None)
        usage_dict = extract_usage_metadata_native(usage_obj)
        self.publish(RequestFinished, request_id, response=response, status='success', usage=usage_dict)
        candidates = getattr(response, 'candidates', None)
        if not candidates or not hasattr(candidates[0], 'content') or not hasattr(candidates[0].content, 'parts'):
            block_reason = None
            block_reason_message = None
            prompt_feedback = getattr(response, 'prompt_feedback', None)
            if prompt_feedback is not None:
                block_reason = getattr(prompt_feedback, 'block_reason', None)
                block_reason_message = getattr(prompt_feedback, 'block_reason_message', None)
            details = {
                "message": "Gemini API returned an empty or incomplete response.",
                "block_reason": str(block_reason) if block_reason else None,
                "block_reason_message": block_reason_message
            }
            self.publish(EmptyResponseEvent, request_id, details=details)
            return True, response, usage_dict, []
        parts_raw = candidates[0].content.parts
        parts = []
        for part in parts_raw:
            if self.cancel_event is not None and self.cancel_event.is_set():
                break
            if hasattr(part, 'function_call') and part.function_call:
                parts.append(FunctionCallMessagePart(
                    tool_call_id=getattr(part.function_call, 'id', ''),
                    name=getattr(part.function_call, 'name', ''),
                    arguments=getattr(part.function_call, 'args', {})
                ))
            elif getattr(part, 'text', None) is not None:
                parts.append(TextMessagePart(content=part.text))
        return False, response, usage_dict, parts

    def _run_generation(self, messages_or_prompt: Union[List[Dict[str, Any]], str], system_prompt: Optional[str]=None, tools=None, schemas=None, **kwargs):
        request_id = str(uuid.uuid4())
        self.tools_adapter.event_bus = self.event_bus
        try:
            self._process_prompt_and_system(messages_or_prompt, system_prompt)
            self.publish(GenerationStarted, request_id, conversation_history=self.get_history())
            config, conversation_contents, client = self._prepare_google_generation(tools, system_prompt)
            if schemas:
                config.tools = schemas
            turn_count = 0
            start_time = time.time()
            while True:
                if self.cancel_event is not None and self.cancel_event.is_set():
                    self.publish(RequestFinished, request_id, response=None, duration=0, status='cancelled', usage={})
                    self.publish(GenerationFinished, request_id, total_turns=turn_count, status='cancelled')
                    break
                done, response, usage_dict, parts = self._process_generation_turn(
                    client, config, conversation_contents, self.tools_adapter, tools, request_id, start_time, kwargs
                )
                turn_count += 1
                if done:
                    self.publish(ResponseReceived, request_id=request_id, parts=parts, tool_results=[], timestamp=time.time(), metadata={"raw_response": response, "usage": usage_dict})
                    self.publish(GenerationFinished, request_id, total_turns=turn_count)
                    break
        except Exception as e:
            self.publish(RequestError, request_id, error=str(e), exception=e, traceback=traceback.format_exc())

    def _prepare_google_generation(self, tools, system_prompt):
        from google.genai import types as genai_types_local
        declarations = generate_tool_declarations(tools) if tools else None
        config_dict = {}
        all_categories = [
            genai_types_local.HarmCategory.HARM_CATEGORY_HARASSMENT,
            genai_types_local.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
            genai_types_local.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
            genai_types_local.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT
        ]
        config_dict["safety_settings"] = [
            genai_types_local.SafetySetting(
                category=cat,
                threshold=genai_types_local.HarmBlockThreshold.BLOCK_NONE
            ) for cat in all_categories
        ]
        if declarations:
            config_dict["tools"] = declarations
        conversation_contents, sys_prompt_from_history = self._conversation_history_to_driver_messages(self._history)
        if system_prompt or sys_prompt_from_history:
            config_dict["system_instruction"] = system_prompt or sys_prompt_from_history
        config = genai_types_local.GenerateContentConfig(**config_dict) if config_dict else None
        client = genai.Client(api_key=self.api_key)
        return config, conversation_contents, client
