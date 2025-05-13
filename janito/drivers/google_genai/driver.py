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
from janito.event_bus.bus import event_bus as default_event_bus
from janito.driver_events import (
    GenerationStarted, GenerationFinished, RequestStarted, RequestFinished, RequestError, ContentPartFound
)
from janito.utils import kwargs_from_locals
from janito.event_bus.queue_bus import QueueEventBusSentinel
import uuid
import datetime
import time
from google import genai
from google.genai import types as genai_types


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
        """
        Initialize the Google Gemini model driver.
        """
        super().__init__(provider_name, model_name)
        self._model_name = model_name
        self._api_key = api_key
        self._tool_executor = tool_executor  # ToolExecutor is now required
        self._thinking_budget = thinking_budget
        self._driver_name = None
        self._request_id = None

    def _publish_event(self, event_cls, **kwargs):
        """
        Generic event publisher. Instantiates and publishes an event of the given class with provided kwargs.
        Always sets driver_name and request_id from the instance attributes.
        """
        kwargs['driver_name'] = self._driver_name
        kwargs['request_id'] = self._request_id
        event = event_cls(**kwargs)
        self._event_bus.publish(event)

    def _handle_parts_interleaved(self, parts, genai_types, conversation_contents, cancel_event=None):
        """
        Process parts in order, interleaving tool calls and content events as they appear.
        Checks cancel_event if provided.
        Returns True if a function call was handled, otherwise False.
        """
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
                conversation_contents.append(genai_types.Content(role="model", parts=[part]))
                function_response_part = genai_types.Part.from_function_response(
                    name=tool_name,
                    response={"result": result}
                )
                conversation_contents.append(genai_types.Content(role="tool", parts=[function_response_part]))
                had_function_call = True
            elif getattr(part, 'text', None) is not None:
                self._publish_event(ContentPartFound, content_part=part.text)
        return had_function_call

    def _process_generation_turn(self, *, prompt, system_prompt, tools, client, genai_types, conversation_contents, cancel_event, kwargs, start_time):
        """
        Process a single turn of the generation loop. Returns True if another turn is needed, False otherwise.
        """
        # Publish request started event
        self._publish_event(RequestStarted, payload={
            'prompt': prompt,
            'system_prompt': system_prompt,
            'tools': tools
        })
        # Generate content from the model
        response = client.models.generate_content(
            model=self._model_name,
            contents=conversation_contents,
            **kwargs
        )
        duration = time.time() - start_time
        usage_obj = getattr(response, 'usage_metadata', None)
        usage_dict = extract_usage_metadata_native(usage_obj)
        # Publish request finished event
        self._publish_event(RequestFinished, response=response, duration=duration, status='success', usage=usage_dict)
        candidates = getattr(response, 'candidates', None)
        if not candidates or not hasattr(candidates[0], 'content') or not hasattr(candidates[0].content, 'parts'):
            raise EmptyResponseError("Gemini API returned an empty or incomplete response.")
        parts = candidates[0].content.parts
        had_function_call = self._handle_parts_interleaved(parts, genai_types, conversation_contents, cancel_event=cancel_event)
        return had_function_call

    def generate(self, prompt: str, system_prompt: Optional[str] = None, tools=None, event_bus=None, **kwargs) -> Optional[str]:
        """
        Generate a response from the Google Gemini model, optionally using tools and a system prompt.
        Handles event publishing and tool execution.
        """
        # --- Event bus and tool executor setup ---
        if hasattr(self._tool_executor, 'event_bus') and event_bus is not None:
            self._tool_executor.event_bus = event_bus
        client = genai.Client(api_key=self._api_key)
        self._request_id = str(uuid.uuid4())
        self._driver_name = self.get_name()
        self._event_bus = event_bus if event_bus is not None else default_event_bus
        self._publish_event(GenerationStarted, prompt=prompt)

        # --- Tool and config preparation ---
        genai_types_local = genai_types
        if tools:
            declarations = generate_tool_declarations(tools)
            config_dict = {
                "tools": declarations,
            }
            if system_prompt:
                config_dict["system_instruction"] = system_prompt
            kwargs['config'] = genai_types_local.GenerateContentConfig(**config_dict)

        # --- Prepare conversation contents ---
        conversation_contents = [genai_types_local.Content(role="user", parts=[genai_types_local.Part(text=prompt)])]
        cancel_event = kwargs.pop('cancel_event', None)
        try:
            turn_count = 0
            start_time = time.time()
            while True:
                # --- Early return if cancelled ---
                if cancel_event is not None and cancel_event.is_set():
                    self._publish_event(RequestFinished, response=None, duration=0, status='cancelled', usage={})
                    return None
                turn_count += 1
                # Remove keys that should not be passed to the API
                kwargs.pop('raw', None)
                kwargs.pop('cancel_event', None)
                # --- Process a single turn ---
                another_turn = self._process_generation_turn(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    tools=tools,
                    client=client,
                    genai_types=genai_types_local,
                    conversation_contents=conversation_contents,
                    cancel_event=cancel_event,
                    kwargs=kwargs,
                    start_time=start_time
                )
                if another_turn:
                    continue  # Continue the loop for the next model response
                self._publish_event(GenerationFinished, total_turns=turn_count)
                break
        except Exception as e:
            self._publish_event(RequestError, error=str(e), exception=e)
            raise e
        finally:
            # --- Publish sentinel event if using a QueueEventBus ---
            try:
                if hasattr(self, '_event_bus') and hasattr(self._event_bus, 'publish'):
                    self._event_bus.publish(QueueEventBusSentinel())
            except Exception:
                pass
