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
import uuid
from janito.event_bus.bus import event_bus as default_event_bus
from janito.driver_events import (
    GenerationStarted, GenerationFinished, RequestStarted, RequestFinished, RequestError, ContentPartFound
)
from janito.utils import kwargs_from_locals
from janito.event_bus.queue_bus import QueueEventBusSentinel

class OpenAIModelDriver(LLMDriver):
    def __init__(self, provider_name: str, model_name: str, api_key: str, tool_executor):
        """
        Initialize the OpenAI model driver.
        """
        super().__init__(provider_name, model_name)
        self._api_key = api_key
        self._tool_executor = tool_executor  # ToolExecutor is now required
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

    def _handle_tool_calls(self, tool_calls, messages, cancel_event=None):
        """
        Handle tool calls by executing the corresponding tools and appending results to the message history.
        """
        tool_results = []
        for tool_call in tool_calls:
            if cancel_event is not None and cancel_event.is_set():
                break  # Abort tool execution if cancelled
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

    def _handle_content(self, content):
        """
        Publish content part found event if content is not None.
        """
        if content is not None:
            self._publish_event(ContentPartFound, content_part=content)
        return content

    def _call_openai(self, prompt, system_prompt, **kwargs):
        import openai
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
        """
        Extract all direct, non-private attributes from the usage object as a flat dict using their native names.
        Mimics the behavior of the Google GenAI driver's usage extraction.
        """
        usage_obj = getattr(response, 'usage', None)
        if usage_obj is None:
            return {}
        result = {}
        for attr in dir(usage_obj):
            if attr.startswith("_") or attr == "__class__":
                continue
            value = getattr(usage_obj, attr)
            # Only include simple types and lists of simple types
            if isinstance(value, (str, int, float, bool, type(None))):
                result[attr] = value
            elif isinstance(value, list):
                if all(isinstance(i, (str, int, float, bool, type(None))) for i in value):
                    result[attr] = value
        return result

    def _process_generation_turn(self, *, prompt, system_prompt, tools, messages, cancel_event, kwargs, start_time):
        """
        Process a single turn of the generation loop. Returns True if another turn is needed, False otherwise.
        """
        self._publish_event(RequestStarted, payload={
            'prompt': prompt,
            'system_prompt': system_prompt,
            'tools': tools
        })
        response = self._call_openai(None, None, messages=messages, **kwargs)
        duration = time.time() - start_time
        usage_dict = self._extract_usage(response)
        self._publish_event(RequestFinished, response=response, duration=duration, status='success', usage=usage_dict)
        message = response.choices[0].message
        content = message.content
        self._handle_content(content)
        tool_calls = getattr(message, 'tool_calls', None)
        if tool_calls:
            assistant_msg = {
                "role": "assistant",
                "content": content,
                "tool_calls": [tc.to_dict() if hasattr(tc, 'to_dict') else dict(tc.__dict__) for tc in tool_calls]
            }
            messages.append(assistant_msg)
            self._handle_tool_calls(tool_calls, messages, cancel_event=cancel_event)
            if cancel_event is not None and cancel_event.is_set():
                return None  # Abort if cancelled
            return True  # Continue the loop for the next model response
        self._publish_event(GenerationFinished, total_turns=1)
        return False

    def generate(self, prompt: str, system_prompt: Optional[str] = None, tools=None, event_bus=None, **kwargs) -> Optional[str]:
        """
        Generate a response from the OpenAI model, optionally using tools and a system prompt.
        Handles event publishing and tool execution.
        """
        # --- Event bus and tool executor setup ---
        if hasattr(self._tool_executor, 'event_bus') and event_bus is not None:
            self._tool_executor.event_bus = event_bus
        self._request_id = str(uuid.uuid4())
        self._driver_name = self.get_name()
        self._event_bus = event_bus if event_bus is not None else default_event_bus
        self._publish_event(GenerationStarted, prompt=prompt)

        # --- Tool and config preparation ---
        if tools:
            schemas = generate_tool_schemas(tools)
            kwargs['tools'] = schemas

        # --- Prepare conversation history ---
        conversation_history = []
        if system_prompt:
            conversation_history.append({"role": "system", "content": system_prompt})
        conversation_history.append({"role": "user", "content": prompt})
        messages = conversation_history[:]
        cancel_event = kwargs.pop('cancel_event', None)
        try:
            start_time = time.time()
            while True:
                # --- Early return if cancelled ---
                if cancel_event is not None and cancel_event.is_set():
                    self._publish_event(RequestFinished, response=None, duration=0, status='cancelled', usage={})
                    return None
                # Remove keys that should not be passed to the API
                kwargs.pop('raw', None)
                kwargs.pop('cancel_event', None)
                # --- Process a single turn ---
                another_turn = self._process_generation_turn(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    tools=tools,
                    messages=messages,
                    cancel_event=cancel_event,
                    kwargs=kwargs,
                    start_time=start_time
                )
                if another_turn:
                    continue  # Continue the loop for the next model response
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
