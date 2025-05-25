import uuid
import traceback
from janito.llm.driver import LLMDriver
from janito.llm.driver_input import DriverInput
from janito.driver_events import RequestStarted, RequestFinished, RequestError, ContentPartFound, ResponseReceived

# Safe import of openai SDK
try:
    import openai
    DRIVER_AVAILABLE = True
    DRIVER_UNAVAILABLE_REASON = None
except ImportError:
    DRIVER_AVAILABLE = False
    DRIVER_UNAVAILABLE_REASON = "Missing dependency: openai (pip install openai)"

class OpenAIModelDriver(LLMDriver):
    """
    OpenAI LLM driver (threaded, queue-based, stateless). Use the input/output queue protocol.
    """
    available = DRIVER_AVAILABLE
    unavailable_reason = DRIVER_UNAVAILABLE_REASON

    def _handle_driver_unavailable(self, request_id):
        self.output_queue.put(RequestError(
            driver_name="openai",
            request_id=request_id,
            error=self.unavailable_reason,
            exception=ImportError(self.unavailable_reason),
            traceback=None
        ))

    def _prepare_api_kwargs(self, config, tool_schema, conversation):
        api_kwargs = {}
        if tool_schema:
            api_kwargs['tools'] = tool_schema
        if getattr(config, 'model', None):
            api_kwargs['model'] = config.model
        if hasattr(config, 'max_tokens') and config.max_tokens is not None:
            api_kwargs['max_tokens'] = int(config.max_tokens)
        for p in ('temperature', 'top_p', 'presence_penalty', 'frequency_penalty', 'stop'):
            v = getattr(config, p, None)
            if v is not None:
                api_kwargs[p] = v
        api_kwargs['messages'] = conversation
        api_kwargs['stream'] = False
        return api_kwargs

    def _emit_response_received(self, config, request_id, result):
        content = result.choices[0].message.content if result.choices else None
        tool_calls = getattr(result.choices[0].message, 'tool_calls', []) if result.choices else []
        timestamp = getattr(result, 'created', None)
        self.output_queue.put(ResponseReceived(
            driver_name="openai",
            request_id=request_id,
            content_parts=[content] if content else [],
            tool_calls=tool_calls,
            tool_results=[],
            timestamp=timestamp,
            metadata={"usage": getattr(result, 'usage', None), "raw_response": result}
        ))

    def _process_input(self, driver_input: DriverInput):
        config = driver_input.config
        conversation = driver_input.conversation_history.get_history()
        tool_schema = driver_input.tool_schema
        request_id = getattr(config, 'request_id', str(uuid.uuid4()))
        if not self.available:
            self._handle_driver_unavailable(request_id)
            return
        self.output_queue.put(RequestStarted(driver_name="openai", request_id=request_id, payload={}))
        try:
            if getattr(config, 'verbose_api', False):
                print(f"[verbose-api] OpenAI API call about to be sent. Model: {getattr(config, 'model', None)}, max_tokens: {getattr(config, 'max_tokens', None)}, tool_schema: {tool_schema is not None}")
            client = openai.OpenAI(api_key=getattr(config, 'api_key', None))
            api_kwargs = self._prepare_api_kwargs(config, tool_schema, conversation)
            if getattr(config, 'verbose_api', False):
                print(f'[OpenAI] API CALL: chat.completions.create(**{api_kwargs})')
            result = client.chat.completions.create(**api_kwargs)
            if getattr(config, 'verbose_api', False):
                print(f'[OpenAI] API RESPONSE: {result}')
            if getattr(config, 'verbose_api', False):
                content = result.choices[0].message.content if result.choices else None
                print(f"[verbose-api] OpenAI Driver: Emitting ResponseReceived with content length: {len(content) if content else 0}")
            self._emit_response_received(config, request_id, result)
        except Exception as ex:
            if getattr(config, 'verbose_api', False):
                print(f'[OpenAI] API ERROR: {ex}')
            self.output_queue.put(RequestError(
                driver_name="openai",
                request_id=request_id,
                error=str(ex),
                exception=ex,
                traceback=traceback.format_exc()
            ))
