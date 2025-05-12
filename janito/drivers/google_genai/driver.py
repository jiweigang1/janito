"""
Google Gemini LLM driver.

This driver handles interaction with the Google Gemini API, including support for tool/function calls and event publishing.

Event Handling:
----------------
When processing model responses, the driver iterates through the returned parts in their original order. Each part may represent a function call or a content segment. Events such as ToolCallStarted, ToolCallFinished, and ContentPartFound are published in the exact sequence they appear in the API response, preserving the interleaving of function calls and content. This ensures that downstream consumers receive events in the true order of model output, which is essential for correct conversational flow and tool execution.
"""
from typing import List, Optional
from janito.llm_driver import LLMDriver
from janito.drivers.google_genai.schema_generator import generate_tool_declarations
import json
from janito.providers.google.errors import EmptyResponseError
from janito.event_bus.bus import event_bus
from janito.driver_events import (
    GenerationStarted, GenerationFinished, RequestStarted, RequestFinished, RequestFinished, RequestError, ContentPartFound
)
from janito.utils import kwargs_from_locals

try:
    from google import genai
    from google.genai import types as genai_types
except ImportError:
    genai = None
    genai_types = None

def extract_usage_metadata_native(usage_obj):
    """
    Extract all direct, non-private attributes from usage_obj as a flat dict using their native names.
    """
    if usage_obj is None:
        return {}
    result = {}
    for attr in dir(usage_obj):
        if attr.startswith("_") or attr == "__class__":
            continue
        value = getattr(usage_obj, attr)
        # Only include simple types and lists, skip nested objects for flatness
        if isinstance(value, (str, int, float, bool, type(None))):
            result[attr] = value
        elif isinstance(value, list):
            # Only include lists of simple types
            if all(isinstance(i, (str, int, float, bool, type(None))) for i in value):
                result[attr] = value
    return result

class GoogleGenaiModelDriver(LLMDriver):
    def __init__(self, provider_name: str, model_name: str, api_key: str, tool_executor, thinking_budget: int = 0):
        super().__init__(provider_name, model_name)
        self._model_name = model_name
        self._api_key = api_key
        self._tool_executor = tool_executor  # ToolExecutor is now required
        self._thinking_budget = thinking_budget

    def _publish_event(self, event):
        event_bus.publish(event)

    def _handle_parts_interleaved(self, parts, request_id, types, contents, cancel_event=None):
        """
        Process parts in order, interleaving tool calls and content events as they appear.
        Checks cancel_event if provided.
        """
        driver_name = self.get_name()
        had_function_call = False
        for part in parts:
            if cancel_event is not None and cancel_event.is_set():
                return had_function_call  # Early exit if cancelled
            if hasattr(part, 'function_call') and part.function_call:
                function_call = part.function_call
                tool_name = function_call.name
                arguments = function_call.args
                if isinstance(arguments, str):
                    arguments = json.loads(arguments)
                result = self._tool_executor.execute_by_name(tool_name, **(arguments or {}))
                contents.append(types.Content(role="model", parts=[part]))
                function_response_part = types.Part.from_function_response(
                    name=tool_name,
                    response={"result": result}
                )
                contents.append(types.Content(role="tool", parts=[function_response_part]))
                had_function_call = True
            elif hasattr(part, 'text') and part.text is not None:
                self._publish_event(ContentPartFound(**kwargs_from_locals('driver_name', 'request_id'), content_part=part.text))
        return had_function_call

    def generate(self, prompt: str, system_prompt: Optional[str] = None, tools=None, **kwargs) -> Optional[str]:
        import uuid, datetime, time
        if genai is None or genai_types is None:
            raise ImportError("google-genai package is not installed.")
        client = genai.Client(api_key=self._api_key)
        types = genai_types
        request_id = str(uuid.uuid4())
        driver_name = self.get_name()
        self._set_latest_event("Sending request to Google GenAI...")
        self._publish_event(GenerationStarted(**kwargs_from_locals('driver_name', 'request_id', 'prompt')))
        self._publish_event(RequestStarted(**kwargs_from_locals('driver_name', 'request_id'), payload=prompt))
        if tools:
            declarations = generate_tool_declarations(tools)
            config_dict = {
                "tools": declarations,
            }
            if system_prompt:
                config_dict["system_instruction"] = system_prompt
            kwargs['config'] = types.GenerateContentConfig(**config_dict)
        contents = []
        contents.append(types.Content(role="user", parts=[types.Part(text=prompt)]))
        cancel_event = kwargs.pop('cancel_event', None)
        try:
            raw = kwargs.pop('raw', False)
            turn_count = 0
            start_time = time.time()
            while True:
                if cancel_event is not None and cancel_event.is_set():
                    self._set_latest_event("Request cancelled.")
                    self._publish_event(RequestFinished(**kwargs_from_locals('driver_name', 'request_id', 'response', 'duration'), status='cancelled', usage={}))
                    return None
                turn_count += 1
                if turn_count > 3:
                    break
                self._set_latest_event("Waiting for Google GenAI response...")
                response = self._generate_content(client, contents, **kwargs)
                duration = time.time() - start_time
                self._set_latest_event("Received response from Google GenAI.")
                usage_obj = getattr(response, 'usage_metadata', None)
                usage_dict = extract_usage_metadata_native(usage_obj)
                self._publish_event(RequestFinished(**kwargs_from_locals('driver_name', 'request_id', 'response', 'duration'), status='success', usage=usage_dict))
                candidates = getattr(response, 'candidates', None)
                if not candidates or not hasattr(candidates[0], 'content') or not hasattr(candidates[0].content, 'parts'):
                    raise EmptyResponseError("Gemini API returned an empty or incomplete response.")
                parts = candidates[0].content.parts
                had_function_call = self._handle_parts_interleaved(parts, request_id, types, contents, cancel_event=cancel_event)
                if had_function_call:
                    self._set_latest_event("Processing function call...")
                    continue  # Continue the loop for the next model response
                self._publish_event(GenerationFinished(**kwargs_from_locals('driver_name', 'request_id'), total_turns=turn_count))
                break
        except Exception as e:
            driver_name = self.get_name()
            self._publish_event(RequestError(**kwargs_from_locals('driver_name', 'request_id'), error=str(e), exception=e))
            raise e

    def _generate_content(self, client, contents, **kwargs):
        kwargs.pop('raw', None)
        kwargs.pop('cancel_event', None)
        return client.models.generate_content(
            model=self._model_name,
            contents=contents,
            **kwargs
        )
