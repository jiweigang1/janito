import uuid
import traceback
from rich import pretty
import os
from janito.llm.driver import LLMDriver
from janito.llm.driver_input import DriverInput
from janito.driver_events import RequestFinished, RequestStatus, RateLimitRetry

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
            "reasoning_effort",
        ):
            v = getattr(config, p, None)
            if v is not None:
                api_kwargs[p] = v
        api_kwargs["messages"] = conversation
        api_kwargs["stream"] = False
        return api_kwargs

    def _call_api(self, driver_input: DriverInput):
        """Call the OpenAI-compatible chat completion endpoint.

        Implements automatic retry logic when the provider returns a *retriable*
        HTTP 429 or ``RESOURCE_EXHAUSTED`` error **that is not caused by quota
        exhaustion**. A ``RateLimitRetry`` driver event is emitted each time a
        retry is scheduled so that user-interfaces can inform the user about
        the wait.

        OpenAI uses the 429 status code both for temporary rate-limit errors *and*
        for permanent quota-exceeded errors (``insufficient_quota``).  Retrying
        the latter is pointless, so we inspect the error payload for
        ``insufficient_quota`` or common quota-exceeded wording and treat those
        as fatal, bubbling them up as a regular RequestFinished/ERROR instead of
        emitting a RateLimitRetry.
        """
        cancel_event = getattr(driver_input, "cancel_event", None)
        config = driver_input.config
        conversation = self.convert_history_to_api_messages(
            driver_input.conversation_history
        )
        request_id = getattr(config, "request_id", None)
        if config.verbose_api:
            tool_adapter_name = type(self.tools_adapter).__name__ if self.tools_adapter else None
            tool_names = []
            if self.tools_adapter and hasattr(self.tools_adapter, "list_tools"):
                try:
                    tool_names = self.tools_adapter.list_tools()
                except Exception:
                    tool_names = ["<error retrieving tools>"]
            print(
                f"[verbose-api] OpenAI API call about to be sent. Model: {config.model}, max_tokens: {config.max_tokens}, tools_adapter: {tool_adapter_name}, tool_names: {tool_names}",
                flush=True,
            )
        import time, re, json

        client = self._instantiate_openai_client(config)
        api_kwargs = self._prepare_api_kwargs(config, conversation)
        max_retries = getattr(config, "max_retries", 3)
        attempt = 1
        while True:
            try:
                if config.verbose_api:
                    print(
                        f"[OpenAI] API CALL (attempt {attempt}/{max_retries}): chat.completions.create(**{api_kwargs})",
                        flush=True,
                    )
                if self._check_cancel(cancel_event, request_id, before_call=True):
                    return None
                result = client.chat.completions.create(**api_kwargs)
                if self._check_cancel(cancel_event, request_id, before_call=False):
                    return None
                # Success path
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
                # Check for rate-limit errors (HTTP 429 or RESOURCE_EXHAUSTED)
                status_code = getattr(e, "status_code", None)
                err_str = str(e)
                # Determine if this is a retriable rate-limit error (HTTP 429) or a non-retriable
                # quota exhaustion error. OpenAI returns the same 429 status code for both, so we
                # additionally check for the ``insufficient_quota`` code or typical quota-related
                # strings in the error message. If the error is quota-related we treat it as fatal
                # so that the caller can surface a proper error message instead of silently
                # retrying forever.
                lower_err = err_str.lower()
                is_insufficient_quota = (
                    "insufficient_quota" in lower_err
                    or "exceeded your current quota" in lower_err
                )
                is_rate_limit = (
                    (status_code == 429 or "error code: 429" in lower_err or "resource_exhausted" in lower_err)
                    and not is_insufficient_quota
                )
                if not is_rate_limit or attempt > max_retries:
                    # If it's not a rate-limit error or we've exhausted retries, handle as fatal
                    self._handle_fatal_exception(e, config, api_kwargs)
                # Parse retry delay from error message (default 1s)
                retry_delay = self._extract_retry_delay_seconds(e)
                if retry_delay is None:
                    # simple exponential backoff if not provided
                    retry_delay = min(2 ** (attempt - 1), 30)
                # Emit RateLimitRetry event so UIs can show a spinner / message
                self.output_queue.put(
                    RateLimitRetry(
                        driver_name=self.__class__.__name__,
                        request_id=request_id,
                        attempt=attempt,
                        retry_delay=retry_delay,
                        error=err_str,
                        details={},
                    )
                )
                if config.verbose_api:
                    print(
                        f"[OpenAI][RateLimit] Attempt {attempt}/{max_retries} failed with rate-limit. Waiting {retry_delay}s before retry.",
                        flush=True,
                    )
                # Wait while still allowing cancellation
                start_wait = time.time()
                while time.time() - start_wait < retry_delay:
                    if self._check_cancel(cancel_event, request_id, before_call=False):
                        return None
                    time.sleep(0.1)
                attempt += 1
                continue
            # console with large JSON payloads when the service returns HTTP 429.
            # We still surface the exception to the caller so that standard error
            # handling (e.g. retries in higher-level code) continues to work.
            status_code = getattr(e, "status_code", None)
            err_str = str(e)
            is_rate_limit = (
                status_code == 429
                or "Error code: 429" in err_str
                or "RESOURCE_EXHAUSTED" in err_str
            )
            is_verbose = getattr(config, "verbose_api", False)

            # Only print the full diagnostics if the user explicitly requested
            # verbose output or if the problem is not a rate-limit situation.
            if is_verbose or not is_rate_limit:
                print(f"[ERROR] Exception during OpenAI API call: {e}", flush=True)
                print(f"[ERROR] config: {config}", flush=True)
                print(
                    f"[ERROR] api_kwargs: {api_kwargs if 'api_kwargs' in locals() else 'N/A'}",
                    flush=True,
                )
                import traceback

                print("[ERROR] Full stack trace:", flush=True)
                print(traceback.format_exc(), flush=True)
            # Re-raise so that the calling logic can convert this into a
            # RequestFinished event with status=ERROR.
            raise

    def _extract_retry_delay_seconds(self, exception) -> float | None:
        """Extract the retry delay in seconds from the provider error response.

        Handles both the Google Gemini style ``RetryInfo`` protobuf (where it's a
        ``retryDelay: '41s'`` string in JSON) and any number found after the word
        ``retryDelay``. Returns ``None`` if no delay could be parsed.
        """
        import re, json, math

        try:
            # Some SDKs expose the raw response JSON on e.args[0]
            if hasattr(exception, "response") and hasattr(exception.response, "text"):
                payload = exception.response.text
            else:
                payload = str(exception)
            # Look for 'retryDelay': '41s' or similar
            m = re.search(r"retryDelay['\"]?\s*[:=]\s*['\"]?(\d+(?:\.\d+)?)(s)?", payload)
            if m:
                return float(m.group(1))
            # Fallback: generic number of seconds in the message
            m2 = re.search(r"(\d+(?:\.\d+)?)\s*s(?:econds)?", payload)
            if m2:
                return float(m2.group(1))
        except Exception:
            pass
        return None

    def _handle_fatal_exception(self, e, config, api_kwargs):
        """Common path for unrecoverable exceptions.

        Prints diagnostics (respecting ``verbose_api``) then re-raises the
        exception so standard error handling in ``LLMDriver`` continues.
        """
        is_verbose = getattr(config, "verbose_api", False)
        if is_verbose:
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

            # HTTP debug wrapper
            if os.environ.get("OPENAI_DEBUG_HTTP", "0") == "1":
                from http.client import HTTPConnection
                HTTPConnection.debuglevel = 1
                import logging
                logging.basicConfig()
                logging.getLogger().setLevel(logging.DEBUG)
                requests_log = logging.getLogger("http.client")
                requests_log.setLevel(logging.DEBUG)
                requests_log.propagate = True
                print("[OpenAIModelDriver] HTTP debug enabled via OPENAI_DEBUG_HTTP=1", flush=True)

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
                    {"role": "assistant", "content": "", "tool_calls": tool_calls}
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
        # Post-processing: Google Gemini API (OpenAI-compatible) rejects null content. Replace None with empty string.
        for m in api_messages:
            if m.get("content", None) is None:
                m["content"] = ""
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
