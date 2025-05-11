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

    def generate(self, prompt: str, system_prompt: Optional[str] = None, tools=None, **kwargs) -> str:
        import uuid, datetime, time
        if genai is None or genai_types is None:
            raise ImportError("google-genai package is not installed.")
        client = genai.Client(api_key=self._api_key)
        types = genai_types
        request_id = str(uuid.uuid4())
        import datetime
        event_bus.publish(GenerationStarted(self.get_name(), request_id, prompt))
        event_bus.publish(RequestStarted(self.get_name(), request_id, prompt))
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
                event_bus.publish(RequestFinished(self.get_name(), request_id, response, duration, 'success'))
                event_bus.publish(ResponseReceived(self.get_name(), request_id, response))
                usage_obj = getattr(response, 'usage_metadata', None)
                usage_dict = _serialize_usage_metadata(usage_obj)
                # Attach usage_dict to response for downstream access
                try:
                    setattr(response, 'usage', usage_dict)
                except Exception:
                    pass  # If response is not writable, skip attaching usage
                candidates = getattr(response, 'candidates', None)
                if not candidates or not hasattr(candidates[0], 'content') or not hasattr(candidates[0].content, 'parts'):
                    content = response.text if hasattr(response, 'text') else str(response)
                    return content
                parts = candidates[0].content.parts
                function_call_parts = [part for part in parts if part.function_call]
                for part in function_call_parts:
                    function_call = part.function_call
                    tool_name = function_call.name
                    arguments = function_call.args
                    if isinstance(arguments, str):
                        arguments = json.loads(arguments)
                    event_bus.publish(ToolCallStarted(tool_name, request_id, arguments))
                    try:
                        result = self._tool_executor.execute_by_name(tool_name, **(arguments or {}))
                        event_bus.publish(ToolCallFinished(tool_name, request_id, result))
                    except Exception as e:
                        event_bus.publish(RequestError(self.get_name(), request_id, str(e), e))
                    contents.append(types.Content(role="model", parts=[part]))
                    function_response_part = types.Part.from_function_response(
                        name=tool_name,
                        response={"result": result}
                    )
                    contents.append(types.Content(role="tool", parts=[function_response_part]))
                if function_call_parts:
                    continue  # Continue the loop for the next model response
                content_parts = [part.text for part in parts if hasattr(part, 'text') and part.text is not None]
                for part_text in content_parts:
                    event_bus.publish(ContentPartFound(self.get_name(), request_id, part_text))
                content = "\n".join(content_parts)
                event_bus.publish(GenerationFinished(self.get_name(), request_id, prompt, turn_count))
                return content
        except Exception as e:
            event_bus.publish(RequestError(self.get_name(), request_id, str(e), e))
            raise e

    def _generate_content(self, client, contents, **kwargs):
        kwargs.pop('raw', None)
        return client.models.generate_content(
            model=self._model_name,
            contents=contents,
            **kwargs
        )
