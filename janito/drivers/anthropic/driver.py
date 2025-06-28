from janito.llm.driver import LLMDriver
from janito.llm.driver_config import LLMDriverConfig
from janito.driver_events import (
    GenerationStarted,
    GenerationFinished,
    RequestStarted,
    RequestFinished,
    ResponseReceived,
)
from janito.llm.message_parts import TextMessagePart
import uuid
import traceback
import time

# Safe import of anthropic SDK
try:
    import anthropic

    DRIVER_AVAILABLE = True
    DRIVER_UNAVAILABLE_REASON = None
except ImportError:
    DRIVER_AVAILABLE = False
    DRIVER_UNAVAILABLE_REASON = "Missing dependency: anthropic (pip install anthropic)"


class AnthropicModelDriver(LLMDriver):
    available = False
    unavailable_reason = "AnthropicModelDriver is not implemented yet."

    @classmethod
    def is_available(cls):
        return cls.available

    """
    LLMDriver for Anthropic's Claude API (v3), using the anthropic SDK.
    """
    required_config = ["api_key", "model"]

    def __init__(self, tools_adapter=None):
        raise ImportError(self.unavailable_reason)

    def _create_client(self):
        try:
            import anthropic
        except ImportError:
            raise Exception(
                "The 'anthropic' Python SDK is required. Please install via `pip install anthropic`."
            )
        return anthropic.Anthropic(api_key=self.api_key)

    def _run_generation(
        self, messages_or_prompt, system_prompt=None, tools=None, **kwargs
    ):
        request_id = str(uuid.uuid4())
        client = self._create_client()
        try:
            prompt = ""
            if isinstance(messages_or_prompt, str):
                prompt = messages_or_prompt
            elif isinstance(messages_or_prompt, list):
                chat = []
                for msg in messages_or_prompt:
                    if msg.get("role") == "user":
                        chat.append("Human: " + msg.get("content", ""))
                    elif msg.get("role") == "assistant":
                        chat.append("Assistant: " + msg.get("content", ""))
                prompt = "\n".join(chat)
            if system_prompt:
                prompt = f"System: {system_prompt}\n{prompt}"

            self.publish(
                GenerationStarted,
                request_id,
                conversation_history=list(getattr(self, "_history", [])),
            )
            self.publish(RequestStarted, request_id, payload={})
            start_time = time.time()
            response = client.completions.create(
                model=self.model_name,
                max_tokens_to_sample=int(getattr(self.config, "max_response", 1024)),
                prompt=prompt,
                temperature=float(getattr(self.config, "default_temp", 0.7)),
            )
            duration = time.time() - start_time
            content = response.completion if hasattr(response, "completion") else None
            self.publish(
                RequestFinished,
                request_id,
                response=content,
                status=RequestStatus.SUCCESS,
                usage={},
            )
            parts = []
            if content:
                parts.append(TextMessagePart(content=content))
            self.publish(
                ResponseReceived,
                request_id=request_id,
                parts=parts,
                tool_results=[],
                timestamp=time.time(),
                metadata={"raw_response": response},
            )
            self.publish(GenerationFinished, request_id, total_turns=1)
        except Exception as e:
            self.publish(
                RequestFinished,
                request_id,
                status=RequestStatus.ERROR,
                error=str(e),
                exception=e,
                traceback=traceback.format_exc(),
            )
