"""
OpenAI LLM driver.

This driver manages interaction with the OpenAI API, supporting both standard chat completions and tool/function calls.

Event Handling:
----------------
When a model response contains both content and tool calls, the driver always publishes the content event (ContentPartFound) first, followed by any tool call events, regardless of their order in the API response. This is different from the Google Gemini driver, which preserves the original order of parts. This approach ensures that the main content is delivered before any tool execution events for downstream consumers.
"""
import openai
import json
import time
import uuid
import traceback
from typing import Optional, List, Dict, Any, Union
from janito.llm.driver import LLMDriver
from janito.providers.openai.schema_generator import generate_tool_schemas
from janito.driver_events import (
    GenerationStarted, GenerationFinished, RequestStarted, RequestFinished, RequestError, ContentPartFound
)
from janito.tools.adapters.local.adapter import LocalToolsAdapter

from janito.llm.driver_config import LLMDriverConfig

class OpenAIModelDriver(LLMDriver):
    """
    Model driver for OpenAI-compatible language models.
    Handles API interaction, conversation history, tool/function calls, and
    dynamic configuration parameters such as max_tokens, temperature, and base_url.
    Inherits from LLMDriver for cross-provider compatibility and interface compliance.
    """
    name = "openai"
    # Which fields to extract from config and LLMDriverConfig
    driver_fields = {"max_tokens", "temperature", "top_p", "presence_penalty", "frequency_penalty", "stop", "base_url", "api_key"}
    def __init__(self, driver_config: LLMDriverConfig, user_prompt: str, conversation_history=None, tools_adapter: LocalToolsAdapter = None):
        super().__init__(driver_config, user_prompt=user_prompt, conversation_history=conversation_history, tools_adapter=tools_adapter)
        self.config = driver_config
        self.base_url = driver_config.base_url

    def _create_client(self):
        import openai
        kwargs = {"api_key": self.config.api_key}
        if self.base_url:
            kwargs["base_url"] = self.base_url
        return openai.OpenAI(**kwargs)

    def get_history(self):
        return list(getattr(self, '_history', []))

    def _add_to_history(self, message: Dict[str, Any]):
        self._history.append(message)

    def _handle_function_call(self, tool_call, tool_executor):
        func = tool_call.function
        try:
            tool_name = func.name
            arguments = func.arguments
        except AttributeError as e:
            raise ValueError(f"OpenAI tool_call.function missing required attribute ({e.args[0]}): {tool_call}")
        tool_call_id = tool_call.id if hasattr(tool_call, 'id') else None
        if tool_name is None:
            raise ValueError(f"OpenAI tool_call.function .name is None: {tool_call}")
        if arguments is None:
            raise ValueError(f"OpenAI tool_call.function .arguments is None: {tool_call}")

        # Explicit checks for required fields
        if not tool_call_id:
            raise ValueError("tool_call.id is missing or None in tool_call: {}".format(tool_call))
        if not tool_name:
            raise ValueError("tool_name is missing or None in tool_call: {}".format(tool_call))

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
            "tool_call_id": tool_call_id,
            "name": tool_name,
            "content": content
        }
        self._add_to_history(tool_result_msg)

    def _handle_content_part(self, content, request_id):
        self.publish(ContentPartFound, request_id, content_part=content)
        assistant_msg = {
            "role": "assistant",
            "content": content
        }
        self._add_to_history(assistant_msg)

    def _get_max_tokens(self):
        if self.config is not None and getattr(self.config, "max_tokens", None) not in (None, '', 'N/A'):
            try:
                return int(self.config.max_tokens)
            except Exception:
                return None
        return None

    def _send_api_request(self, client, messages, schemas, **api_kwargs):
        # Pass temperature from api_kwargs if present, default to 0
        if 'temperature' not in api_kwargs:
            pass  # Do not set temperature if not specified; use provider default
        if schemas:
            api_kwargs['tools'] = schemas
            if 'tool_choice' not in api_kwargs:
                api_kwargs['tool_choice'] = 'auto'
        # Set max_tokens if available
        max_tokens = self._get_max_tokens()
        if max_tokens is not None:
            api_kwargs['max_tokens'] = max_tokens
        api_kwargs['model'] = self.model_name
        api_kwargs['messages'] = messages
        api_kwargs['stream'] = False
        try:
            result = client.chat.completions.create(**api_kwargs)
            return result
        except Exception as ex:
            raise

    def _extract_usage(self, usage):
        usage_dict = {}
        if usage:
            for attr in dir(usage):
                if attr.startswith('_') or attr == '__class__':
                    continue
                value = getattr(usage, attr)
                if isinstance(value, (str, int, float, bool, type(None))):
                    usage_dict[attr] = value
                elif isinstance(value, list):
                    if all(isinstance(i, (str, int, float, bool, type(None))) for i in value):
                        usage_dict[attr] = value
        return usage_dict

    def _process_tool_calls(self, tool_calls, tool_executor):
        had_function_call = False
        for tool_call in tool_calls:
            if self.cancel_event is not None and self.cancel_event.is_set():
                break
            self._handle_function_call(tool_call, self.tools_adapter)
            had_function_call = True
        return had_function_call

    def _process_generation_turn(self, client, schemas, tools, request_id, start_time, kwargs, tool_executor):
        api_kwargs = dict(kwargs)
        api_kwargs.pop('raw', None)
        self.publish(RequestStarted, request_id, payload={'tools': tools})
        messages = self.get_history()
        response = self._send_api_request(client, messages, schemas, **api_kwargs)
        usage_dict = self._extract_usage(getattr(response, 'usage', None))
        self.publish(RequestFinished, request_id, response=response, status='success', usage=usage_dict)
        message = response.choices[0].message
        content = message.content
        self._process_content_part(content, request_id)
        tool_calls = getattr(message, 'tool_calls', None)
        return self._process_tool_calls_in_generation(tool_calls, content)

    def _process_content_part(self, content, request_id):
        if content is not None:
            self._handle_content_part(content, request_id)

    def _process_tool_calls_in_generation(self, tool_calls, content):
        if tool_calls:
            assistant_msg = {
                "role": "assistant",
                "content": content,
                "tool_calls": [tc.to_dict() if hasattr(tc, 'to_dict') else dict(tc.__dict__) for tc in tool_calls]
            }
            tool_result_msgs = [self._build_tool_result_msg(tc) for tc in tool_calls]
            self._add_to_history(assistant_msg)
            for msg in tool_result_msgs:
                self._add_to_history(msg)
            return True, None
        return False, None

    def _build_tool_result_msg(self, tool_call):
        func = tool_call.function
        try:
            tool_name = func.name
            arguments = func.arguments
        except AttributeError as e:
            raise ValueError(f"OpenAI tool_call.function missing required attribute ({e.args[0]}): {tool_call}")
        tool_call_id = tool_call.id if hasattr(tool_call, 'id') else None
        if tool_name is None:
            raise ValueError(f"OpenAI tool_call.function .name is None: {tool_call}")
        if arguments is None:
            raise ValueError(f"OpenAI tool_call.function .arguments is None: {tool_call}")
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except Exception:
                arguments = {}
        try:
            result = self.tools_adapter.execute_by_name(tool_name, **(arguments or {}))
            tool_content = str(result)
        except Exception as e:
            tool_content = f"Tool execution error: {e}"
        return {
            "role": "tool",
            "tool_call_id": tool_call_id,
            "name": tool_name,
            "content": tool_content
        }

    def _generate_schemas(self, tools):
        # OpenAI and OpenAI-compatible drivers use OpenAISchemaGenerator
        from janito.providers.openai.schema_generator import generate_tool_schemas
        return generate_tool_schemas(tools) if tools else None

    def _run_generation(self, messages_or_prompt: Union[List[Dict[str, Any]], str], system_prompt: Optional[str]=None, tools=None, schemas=None, **kwargs):
        request_id = str(uuid.uuid4())
        self.tools_adapter.event_bus = self.event_bus
        try:
            # Do not clear internal history here; accumulate across turns
            if isinstance(messages_or_prompt, str):
                user_msg = {"role": "user", "content": messages_or_prompt}
                self._add_to_history(user_msg)
            elif isinstance(messages_or_prompt, list):
                for msg in messages_or_prompt:
                    self._add_to_history(dict(msg))
            if system_prompt:
                # Ensure system prompt is the first message if provided
                if not self._history or self._history[0].get('role') != 'system':
                    self._history.insert(0, {"role": "system", "content": system_prompt})
            self.publish(GenerationStarted, request_id, conversation_history=self.get_history())
            # schemas now passed as argument, no longer generated here
            client = self._create_client()
            turn_count = 0
            while True:
                if self.cancel_event is not None and self.cancel_event.is_set():
                    self.publish(RequestFinished, request_id, response=None, status='cancelled', usage={})
                    self.publish(GenerationFinished, request_id, total_turns=turn_count, status='cancelled')
                    break
                had_function_call, _ = self._process_generation_turn(
                    client, schemas, tools, request_id, None, kwargs, self.tools_adapter
                )
                turn_count += 1
                if had_function_call and (self.cancel_event is None or not self.cancel_event.is_set()):
                    continue
                self.publish(GenerationFinished, request_id, total_turns=turn_count)
                break
        except Exception as e:
            self.publish(RequestError, request_id, error=str(e), exception=e, traceback=traceback.format_exc())
