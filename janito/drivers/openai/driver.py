import uuid
import traceback
from rich import pretty
from janito.llm.driver import LLMDriver
from janito.llm.driver_input import DriverInput
from janito.driver_events import RequestFinished, RequestStatus

# Safe import of openai SDK
try:
    import openai

    DRIVER_AVAILABLE = True
    DRIVER_UNAVAILABLE_REASON = None
except ImportError:
    DRIVER_AVAILABLE = False
    DRIVER_UNAVAILABLE_REASON = "Missing dependency: openai (pip install openai)"


class OpenAIModelDriver(LLMDriver):
    def _get_message_from_result(self, result):
        """Extract the message object from the provider result (OpenAI-specific)."""
        if hasattr(result, "choices") and result.choices:
            return result.choices[0].message
        return None

    """
    OpenAI LLM driver (threaded, queue-based, stateless). Uses input/output queues accessible via instance attributes.
    """
    available = DRIVER_AVAILABLE
    unavailable_reason = DRIVER_UNAVAILABLE_REASON

    def __init__(self, tools_adapter=None, provider_name=None):
        super().__init__(tools_adapter=tools_adapter, provider_name=provider_name)

    def _prepare_api_kwargs(self, config, conversation):
        """
        Prepares API kwargs for OpenAI, including tool schemas if tools_adapter is present,
        and OpenAI-specific arguments (model, max_tokens, temperature, etc.).
        """
        api_kwargs = {}
        # Tool schemas (moved from base)
        if self.tools_adapter:
            try:
                from janito.providers.openai.schema_generator import (
                    generate_tool_schemas,
                )

                tool_classes = self.tools_adapter.get_tool_classes()
                tool_schemas = generate_tool_schemas(tool_classes)
                api_kwargs["tools"] = tool_schemas
            except Exception as e:
                api_kwargs["tools"] = []
                if hasattr(config, "verbose_api") and config.verbose_api:
                    print(f"[OpenAIModelDriver] Tool schema generation failed: {e}")
        # OpenAI-specific parameters
        if config.model:
            api_kwargs["model"] = config.model
        # Prefer max_completion_tokens if present, else fallback to max_tokens (for backward compatibility)
        if (
            hasattr(config, "max_completion_tokens")
            and config.max_completion_tokens is not None
        ):
            api_kwargs["max_completion_tokens"] = int(config.max_completion_tokens)
        elif hasattr(config, "max_tokens") and config.max_tokens is not None:
            # For models that do not support 'max_tokens', map to 'max_completion_tokens'
            api_kwargs["max_completion_tokens"] = int(config.max_tokens)
        for p in (
            "temperature",
            "top_p",
            "presence_penalty",
            "frequency_penalty",
            "stop",
        ):
            v = getattr(config, p, None)
            if v is not None:
                api_kwargs[p] = v
        api_kwargs["messages"] = conversation
        api_kwargs["stream"] = False
        return api_kwargs

    def _call_api(self, driver_input: DriverInput):
        cancel_event = getattr(driver_input, "cancel_event", None)
        config = driver_input.config
        conversation = self.convert_history_to_api_messages(
            driver_input.conversation_history
        )
        request_id = getattr(config, "request_id", None)
        if config.verbose_api:
            print(
                f"[verbose-api] OpenAI API call about to be sent. Model: {config.model}, max_tokens: {config.max_tokens}, tools_adapter: {type(self.tools_adapter).__name__ if self.tools_adapter else None}",
                flush=True,
            )
        try:
            client = self._instantiate_openai_client(config)
            api_kwargs = self._prepare_api_kwargs(config, conversation)
            if config.verbose_api:
                print(
                    f"[OpenAI] API CALL: chat.completions.create(**{api_kwargs})",
                    flush=True,
                )
            if self._check_cancel(cancel_event, request_id, before_call=True):
                return None
            result = client.chat.completions.create(**api_kwargs)
            if self._check_cancel(cancel_event, request_id, before_call=False):
                return None
            self._print_verbose_result(config, result)
            usage_dict = self._extract_usage(result)
            if config.verbose_api:
                print(
                    f"[OpenAI][DEBUG] Attaching usage info to RequestFinished: {usage_dict}",
                    flush=True,
                )
            self.output_queue.put(
                RequestFinished(
                    driver_name=self.__class__.__name__,
                    request_id=request_id,
                    response=result,
                    status=RequestStatus.SUCCESS,
                    usage=usage_dict,
                )
            )
            if config.verbose_api:
                pretty.install()
                print("[OpenAI] API RESPONSE:", flush=True)
                pretty.pprint(result)
            return result
        except Exception as e:
            print(f"[ERROR] Exception during OpenAI API call: {e}", flush=True)
            print(f"[ERROR] config: {config}", flush=True)
            print(
                f"[ERROR] api_kwargs: {api_kwargs if 'api_kwargs' in locals() else 'N/A'}",
                flush=True,
            )
            import traceback

            print("[ERROR] Full stack trace:", flush=True)
            print(traceback.format_exc(), flush=True)
            raise

    def _instantiate_openai_client(self, config):
        try:
            api_key_display = str(config.api_key)
            if api_key_display and len(api_key_display) > 8:
                api_key_display = api_key_display[:4] + "..." + api_key_display[-4:]
            client_kwargs = {"api_key": config.api_key}
            if getattr(config, "base_url", None):
                client_kwargs["base_url"] = config.base_url
            client = openai.OpenAI(**client_kwargs)
            return client
        except Exception as e:
            print(
                f"[ERROR] Exception during OpenAI client instantiation: {e}", flush=True
            )
            import traceback

            print(traceback.format_exc(), flush=True)
            raise

    def _check_cancel(self, cancel_event, request_id, before_call=True):
        if cancel_event is not None and cancel_event.is_set():
            status = RequestStatus.CANCELLED
            reason = (
                "Cancelled before API call"
                if before_call
                else "Cancelled during API call"
            )
            self.output_queue.put(
                RequestFinished(
                    driver_name=self.__class__.__name__,
                    request_id=request_id,
                    status=status,
                    reason=reason,
                )
            )
            return True
        return False

    def _print_verbose_result(self, config, result):
        if config.verbose_api:
            print("[OpenAI] API RAW RESULT:", flush=True)
            pretty.pprint(result)
            if hasattr(result, "__dict__"):
                print("[OpenAI] API RESULT __dict__:", flush=True)
                pretty.pprint(result.__dict__)
            try:
                print("[OpenAI] API RESULT as dict:", dict(result), flush=True)
            except Exception:
                pass
            print(
                f"[OpenAI] API RESULT .usage: {getattr(result, 'usage', None)}",
                flush=True,
            )
            try:
                print(f"[OpenAI] API RESULT ['usage']: {result['usage']}", flush=True)
            except Exception:
                pass
            if not hasattr(result, "usage") or getattr(result, "usage", None) is None:
                print(
                    "[OpenAI][WARNING] No usage info found in API response.", flush=True
                )

    def _extract_usage(self, result):
        usage = getattr(result, "usage", None)
        if usage is not None:
            usage_dict = self._usage_to_dict(usage)
            if usage_dict is None:
                print(
                    "[OpenAI][WARNING] Could not convert usage to dict, using string fallback.",
                    flush=True,
                )
                usage_dict = str(usage)
        else:
            usage_dict = self._extract_usage_from_result_dict(result)
        return usage_dict

    def _usage_to_dict(self, usage):
        if hasattr(usage, "model_dump") and callable(getattr(usage, "model_dump")):
            try:
                return usage.model_dump()
            except Exception:
                pass
        if hasattr(usage, "dict") and callable(getattr(usage, "dict")):
            try:
                return usage.dict()
            except Exception:
                pass
        try:
            return dict(usage)
        except Exception:
            try:
                return vars(usage)
            except Exception:
                pass
        return None

    def _extract_usage_from_result_dict(self, result):
        try:
            return result["usage"]
        except Exception:
            return None

    def convert_history_to_api_messages(self, conversation_history):
        """
        Convert LLMConversationHistory to the list of dicts required by OpenAI's API.
        Handles 'tool_results' and 'tool_calls' roles for compliance.
        """
        import json

        api_messages = []
        for msg in conversation_history.get_history():
            role = msg.get("role")
            content = msg.get("content")
            if role == "tool_results":
                # Expect content to be a list of tool result dicts or a stringified list
                try:
                    results = (
                        json.loads(content) if isinstance(content, str) else content
                    )
                except Exception:
                    results = [content]
                for result in results:
                    # result should be a dict with keys: name, content, tool_call_id
                    if isinstance(result, dict):
                        api_messages.append(
                            {
                                "role": "tool",
                                "content": result.get("content", ""),
                                "name": result.get("name", ""),
                                "tool_call_id": result.get("tool_call_id", ""),
                            }
                        )
                    else:
                        api_messages.append(
                            {
                                "role": "tool",
                                "content": str(result),
                                "name": "",
                                "tool_call_id": "",
                            }
                        )
            elif role == "tool_calls":
                # Convert to assistant message with tool_calls field
                import json

                try:
                    tool_calls = (
                        json.loads(content) if isinstance(content, str) else content
                    )
                except Exception:
                    tool_calls = []
                api_messages.append(
                    {"role": "assistant", "content": None, "tool_calls": tool_calls}
                )
            else:
                # Special handling for 'function' role: extract 'name' from metadata if present
                if role == "function":
                    name = ""
                    if isinstance(msg, dict):
                        metadata = msg.get("metadata", {})
                        name = (
                            metadata.get("name", "")
                            if isinstance(metadata, dict)
                            else ""
                        )
                    api_messages.append(
                        {"role": "tool", "content": content, "name": name}
                    )
                else:
                    api_messages.append(msg)
        return api_messages

    def _convert_completion_message_to_parts(self, message):
        """
        Convert an OpenAI completion message object to a list of MessagePart objects.
        Handles text, tool calls, and can be extended for other types.
        """
        from janito.llm.message_parts import TextMessagePart, FunctionCallMessagePart

        parts = []
        # Text content
        content = getattr(message, "content", None)
        if content:
            parts.append(TextMessagePart(content=content))
        # Tool calls
        tool_calls = getattr(message, "tool_calls", None) or []
        for tool_call in tool_calls:
            parts.append(
                FunctionCallMessagePart(
                    tool_call_id=getattr(tool_call, "id", ""),
                    function=getattr(tool_call, "function", None),
                )
            )
        # Extend here for other message part types if needed
        return parts
