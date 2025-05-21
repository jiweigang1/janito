"""
Google Gemini LLM driver.

This driver handles interaction with the Google Gemini API, including support for tool/function calls and event publishing.

Event Handling:
----------------
When processing model responses, the driver iterates through the returned parts in their original order. Each part may represent a function call or a content segment. Events such as ContentPartFound are published in the exact sequence they appear in the API response, preserving the interleaving of function calls and content. This ensures that downstream consumers receive events in the true order of model output, which is essential for correct conversational flow and tool execution.
"""
import json
import time
import uuid
import traceback
from typing import Optional, List, Dict, Any, Union
from janito.llm.driver import LLMDriver
from janito.drivers.google_genai.schema_generator import generate_tool_declarations
from janito.providers.google.errors import EmptyResponseError
from janito.driver_events import (
    GenerationStarted, GenerationFinished, RequestStarted, RequestFinished, RequestError, ContentPartFound
)
from janito.tool_executor import ToolExecutor
from janito.tool_registry import ToolRegistry
from google import genai
from google.genai import types as genai_types
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
    name = "google_genai"
    def __init__(self, info: LLMDriverConfig, tool_registry: ToolRegistry = None):
        super().__init__('google', info.model, info.api_key, tool_registry)
        self.config = info
        self._history: List[Dict[str, Any]] = []

    def _add_to_history(self, message: Dict[str, Any]):
        self._history.append(message)

    def get_history(self):
        return list(self._history)

    def _conversation_history_to_driver_messages(self, history_msgs: List[Dict[str, Any]]):
        """
        Convert internal history to Google GenAI Content/Part objects.
        Returns (conversation_contents, system_prompt)
        """
        from google.genai import types as genai_types_local
        msgs = list(history_msgs)
        system_prompt = None
        if msgs and isinstance(msgs[0], dict) and msgs[0].get('role') == 'system':
            system_prompt = msgs.pop(0).get('content')
        conversation_contents = []
        for msg in msgs:
            if msg.get("role") == "tool":
                meta = msg.get("metadata", {})
                # Tool call (arguments present, content is None)
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
                # Tool response (content present)
                elif msg.get("content") is not None:
                    conversation_contents.append(
                        genai_types_local.Content(
                            role="tool",
                            parts=[genai_types_local.Part(
                                text=msg.get("content"),
                                function_response={
                                    "name": meta.get("name"),
                                    "response": {"result": msg.get("content")}
                                }
                            )]
                        )
                    )
            else:
                # user, assistant
                conversation_contents.append(
                    genai_types_local.Content(
                        role=msg.get("role"),
                        parts=[genai_types_local.Part(text=msg.get("content"))]
                    )
                )
        return conversation_contents, system_prompt

    def handle_function_call(self, part, conversation_contents, tool_executor):
        function_call = part.function_call
        tool_name = function_call.name
        arguments = function_call.args
        if isinstance(arguments, str):
            arguments = json.loads(arguments)
        try:
            result = tool_executor.execute_by_name(tool_name, **(arguments or {}))
            content = str(result)
        except Exception as e:
            content = f"Tool execution error: {e}"
        conversation_contents.append(genai_types.Content(role="model", parts=[part]))
        function_response_part = genai_types.Part.from_function_response(
            name=tool_name,
            response={"result": content}
        )
        conversation_contents.append(genai_types.Content(role="tool", parts=[function_response_part]))
        # Add tool response to internal history
        self._add_to_history({
            "role": "tool",
            "name": tool_name,
            "content": content,
            "metadata": {"name": tool_name, "arguments": arguments}
        })

    def handle_content_part(self, part, request_id):
        self.publish(ContentPartFound, request_id, content_part=part.text)
        # Add assistant message to internal history
        self._add_to_history({
            "role": "assistant",
            "content": part.text
        })

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
        self.publish(RequestFinished, request_id, response=response, duration=duration, status='success', usage=usage_dict)
        candidates = getattr(response, 'candidates', None)
        if not candidates or not hasattr(candidates[0], 'content') or not hasattr(candidates[0].content, 'parts'):
            raise EmptyResponseError("Gemini API returned an empty or incomplete response.")
        parts = candidates[0].content.parts
        had_function_call = False
        for part in parts:
            if self.cancel_event is not None and self.cancel_event.is_set():
                break
            if hasattr(part, 'function_call') and part.function_call:
                self.handle_function_call(part, conversation_contents, tool_executor)
                had_function_call = True
            elif getattr(part, 'text', None) is not None:
                self.handle_content_part(part, request_id)
        return had_function_call, duration

    def _run_generation(self, messages_or_prompt: Union[List[Dict[str, Any]], str], system_prompt: Optional[str]=None, tools=None, **kwargs):
        """
        Run a conversation using the provided messages or prompt.
        The driver manages its own internal conversation history.
        """
        request_id = str(uuid.uuid4())
        tool_executor = ToolExecutor(registry=self.tool_registry, event_bus=self.event_bus)
        try:
            self._process_prompt_and_system(messages_or_prompt, system_prompt)
            self.publish(GenerationStarted, request_id, conversation_history=self.get_history())
            config, conversation_contents, client = self._prepare_google_generation(tools, system_prompt)
            turn_count = 0
            start_time = time.time()
            while True:
                if self.cancel_event is not None and self.cancel_event.is_set():
                    self.publish(RequestFinished, request_id, response=None, duration=0, status='cancelled', usage={})
                    self.publish(GenerationFinished, request_id, total_turns=turn_count, status='cancelled')
                    break
                had_function_call, _ = self._process_generation_turn(
                    client, config, conversation_contents, tool_executor, tools, request_id, start_time, kwargs
                )
                turn_count += 1
                if had_function_call and (self.cancel_event is None or not self.cancel_event.is_set()):
                    continue  # Continue the loop for the next model response
                self.publish(GenerationFinished, request_id, total_turns=turn_count)
                break
        except Exception as e:
            self.publish(RequestError, request_id, error=str(e), exception=e, traceback=traceback.format_exc())

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

    def _prepare_google_generation(self, tools, system_prompt):
        from google.genai import types as genai_types_local
        declarations = generate_tool_declarations(tools) if tools else None
        config_dict = {}
        if declarations:
            config_dict["tools"] = declarations
        conversation_contents, sys_prompt_from_history = self._conversation_history_to_driver_messages(self._history)
        if system_prompt or sys_prompt_from_history:
            config_dict["system_instruction"] = system_prompt or sys_prompt_from_history
        config = genai_types_local.GenerateContentConfig(**config_dict) if config_dict else None
        client = genai.Client(api_key=self.api_key)
        return config, conversation_contents, client
