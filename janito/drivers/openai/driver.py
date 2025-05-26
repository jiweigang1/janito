import uuid
import traceback
from rich import pretty
from janito.llm.driver import LLMDriver
from janito.llm.driver_input import DriverInput

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

    def __init__(self, input_queue, output_queue, tools_adapter=None):
        super().__init__(input_queue, output_queue)
        self.tools_adapter = tools_adapter

    def _prepare_api_kwargs(self, config, conversation):
        api_kwargs = {}
        if self.tools_adapter:
            try:
                from janito.providers.openai.schema_generator import generate_tool_schemas
                tool_classes = self.tools_adapter.get_tool_classes()
                api_kwargs['tools'] = generate_tool_schemas(tool_classes)
            except Exception as e:
                api_kwargs['tools'] = []
                if config.verbose_api:
                    print(f"[OpenAI] Tool schema generation failed: {e}")
        if config.model:
            api_kwargs['model'] = config.model
        if hasattr(config, 'max_tokens') and config.max_tokens is not None:
            api_kwargs['max_tokens'] = int(config.max_tokens)
        for p in ('temperature', 'top_p', 'presence_penalty', 'frequency_penalty', 'stop'):
            v = config.__getattribute__(p)
            if v is not None:
                api_kwargs[p] = v
        api_kwargs['messages'] = conversation
        api_kwargs['stream'] = False
        return api_kwargs

    def _call_api(self, driver_input: DriverInput):
        config = driver_input.config
        conversation = driver_input.conversation_history.get_history()
        if config.verbose_api:
            print(f"[verbose-api] OpenAI API call about to be sent. Model: {config.model}, max_tokens: {config.max_tokens}, tools_adapter: {self.tools_adapter is not None}")
        client = openai.OpenAI(api_key=config.api_key)
        api_kwargs = self._prepare_api_kwargs(config, conversation)
        if config.verbose_api:
            print(f'[OpenAI] API CALL: chat.completions.create(**{api_kwargs})')
        result = client.chat.completions.create(**api_kwargs)
        if config.verbose_api:
            pretty.install()
            print('[OpenAI] API RESPONSE:')
            pretty.pprint(result)
            content = result.choices[0].message.content if result.choices else None
            print(f"[verbose-api] OpenAI Driver: Emitting ResponseReceived with content length: {len(content) if content else 0}")
        return result

    def _convert_completion_message_to_parts(self, message):
        """
        Convert an OpenAI completion message object to a list of MessagePart objects.
        Handles text, tool calls, and can be extended for other types.
        """
        from janito.llm.message_parts import TextMessagePart, FunctionCallMessagePart
        parts = []
        # Text content
        content = getattr(message, 'content', None)
        if content:
            parts.append(TextMessagePart(content=content))
        # Tool calls
        tool_calls = getattr(message, 'tool_calls', None) or []
        for tool_call in tool_calls:
            parts.append(FunctionCallMessagePart(
                tool_call_id=getattr(tool_call, 'id', ''),
                function=getattr(tool_call, 'function', None)
            ))
        # Extend here for other message part types if needed
        return parts
