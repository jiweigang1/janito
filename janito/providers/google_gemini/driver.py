from typing import List, Optional
from janito.llm_driver import LLMDriver
from janito.providers.google_gemini.schema_generator import generate_tool_declarations
import json
from janito.event_bus.bus import event_bus
from janito.event_types import (
    GenerationStarted, GenerationFinished, RequestStarted, RequestFinished, ResponseReceived, RequestError, ToolCallStarted, ToolCallFinished, ContentPartFound
)

try:
    from google import genai
    from google.genai import types as genai_types
except ImportError:
    genai = None
    genai_types = None

def _serialize_usage_metadata(usage_obj):
    if usage_obj is None:
        return {}
    result = {}
    for attr in dir(usage_obj):
        if attr.startswith("_") or attr == "__class__":
            continue
        value = getattr(usage_obj, attr)
        result[attr] = _serialize_value(value)
    return result

def _serialize_value(value):
    if isinstance(value, list):
        return [_serialize_item(item) for item in value]
    elif _is_enum(value):
        return value.value if hasattr(value, "value") else str(value)
    elif hasattr(value, "__dict__"):
        return {k: _serialize_value(v) for k, v in value.__dict__.items()}
    else:
        return value

def _serialize_item(item):
    if hasattr(item, "__dict__"):
        return {k: (v.value if _is_enum(v) else v) for k, v in item.__dict__.items()}
    return item

def _is_enum(val):
    t = str(type(val))
    return t.endswith("Enum'>") or t.endswith("EnumType'>")

class GoogleGeminiModelDriver(LLMDriver):
    def __init__(self, provider_name: str, model_name: str, api_key: str, tool_executor, thinking_budget: int = 0):
        super().__init__(provider_name, model_name)
        self._model_name = model_name
        self._api_key = api_key
        self._tool_executor = tool_executor  # ToolExecutor is now required
        self._thinking_budget = thinking_budget

    def _publish_event(self, event):
        event_bus.publish(event)

    def _handle_tool_calls(self, parts, request_id, types, contents):
        function_call_parts = [part for part in parts if part.function_call]
        results = []
        for part in function_call_parts:
            function_call = part.function_call
            tool_name = function_call.name
            arguments = function_call.args
            if isinstance(arguments, str):
                arguments = json.loads(arguments)
            self._publish_event(ToolCallStarted(tool_name, request_id, arguments))
            try:
                result = self._tool_executor.execute_by_name(tool_name, **(arguments or {}))
                self._publish_event(ToolCallFinished(tool_name, request_id, result))
            except Exception as e:
                self._publish_event(RequestError(self.get_name(), request_id, str(e), e))
                result = None
            contents.append(types.Content(role="model", parts=[part]))
            function_response_part = types.Part.from_function_response(
                name=tool_name,
                response={"result": result}
            )
            contents.append(types.Content(role="tool", parts=[function_response_part]))
            results.append(result)
        return function_call_parts, results

    def _handle_content_parts(self, parts, request_id):
        content_parts = [part.text for part in parts if hasattr(part, 'text') and part.text is not None]
        for part_text in content_parts:
            self._publish_event(ContentPartFound(self.get_name(), request_id, part_text))
        return "\n".join(content_parts)

    def generate(self, prompt: str, system_prompt: Optional[str] = None, tools=None, **kwargs) -> str:
        import uuid, datetime, time
        if genai is None or genai_types is None:
            raise ImportError("google-genai package is not installed.")
        client = genai.Client(api_key=self._api_key)
        types = genai_types
        request_id = str(uuid.uuid4())
        self._publish_event(GenerationStarted(self.get_name(), request_id, prompt))
        self._publish_event(RequestStarted(self.get_name(), request_id, prompt))
        if tools:
            declarations = generate_tool_declarations(tools)
            config_dict = {
                "tools": declarations,
                "automatic_function_calling": {"disable": True},
            }
            if system_prompt:
                config_dict["system_instruction"] = system_prompt
            kwargs['config'] = types.GenerateContentConfig(**config_dict)
        contents = []
        contents.append(types.Content(role="user", parts=[types.Part(text=prompt)]))
        try:
            raw = kwargs.pop('raw', False)
            turn_count = 0
            start_time = time.time()
            while True:
                turn_count += 1
                if turn_count > 3:
                    break
                response = self._generate_content(client, contents, **kwargs)
                duration = time.time() - start_time
                self._publish_event(RequestFinished(self.get_name(), request_id, response, duration, 'success'))
                self._publish_event(ResponseReceived(self.get_name(), request_id, response))
                usage_obj = getattr(response, 'usage_metadata', None)
                usage_dict = _serialize_usage_metadata(usage_obj)
                try:
                    setattr(response, 'usage', usage_dict)
                except Exception:
                    pass
                candidates = getattr(response, 'candidates', None)
                if not candidates or not hasattr(candidates[0], 'content') or not hasattr(candidates[0].content, 'parts'):
                    content = response.text if hasattr(response, 'text') else str(response)
                    return content
                parts = candidates[0].content.parts
                function_call_parts, _ = self._handle_tool_calls(parts, request_id, types, contents)
                if function_call_parts:
                    continue  # Continue the loop for the next model response
                content = self._handle_content_parts(parts, request_id)
                self._publish_event(GenerationFinished(self.get_name(), request_id, prompt, turn_count))
                return content
        except Exception as e:
            self._publish_event(RequestError(self.get_name(), request_id, str(e), e))
            raise e

    def _generate_content(self, client, contents, **kwargs):
        kwargs.pop('raw', None)
        return client.models.generate_content(
            model=self._model_name,
            contents=contents,
            **kwargs
        )
