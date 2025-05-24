from janito.llm.driver import LLMDriver
from janito.llm.driver_config import LLMDriverConfig
from janito.driver_events import (
    GenerationStarted, GenerationFinished, RequestStarted, RequestFinished, RequestError, ContentPartFound
)
import uuid
import traceback

class AnthropicModelDriver(LLMDriver):
    """
    LLMDriver for Anthropic's Claude API (v3), using the anthropic SDK.
    """
    required_config = ["api_key", "model"]

    def __init__(self, driver_config: LLMDriverConfig, user_prompt: str = None, conversation_history=None, tools_adapter=None):
        super().__init__(driver_config, user_prompt=user_prompt, conversation_history=conversation_history, tools_adapter=tools_adapter)
        self.config = driver_config

    def _create_client(self):
        try:
            import anthropic
        except ImportError:
            raise Exception("The 'anthropic' Python SDK is required. Please install via `pip install anthropic`.")
        return anthropic.Anthropic(api_key=self.api_key)

    def _run_generation(self, messages_or_prompt, system_prompt=None, tools=None, **kwargs):
        request_id = str(uuid.uuid4())
        client = self._create_client()
        try:
            # Anthropic expects a single prompt string, not a message list.
            prompt = ""
            if isinstance(messages_or_prompt, str):
                prompt = messages_or_prompt
            elif isinstance(messages_or_prompt, list):
                # If passed a message history, join as plain chat.
                chat = []
                for msg in messages_or_prompt:
                    if msg.get("role") == "user":
                        chat.append("Human: " + msg.get("content", ""))
                    elif msg.get("role") == "assistant":
                        chat.append("Assistant: " + msg.get("content", ""))
                prompt = "\n".join(chat)
            if system_prompt:
                prompt = f"System: {system_prompt}\n{prompt}"

            self.publish(GenerationStarted, request_id, conversation_history=self.get_history())
            self.publish(RequestStarted, request_id, payload={})

            # Many Claude models stream, but here we use a one-shot for parity to start (add streaming as needed)
            response = client.completions.create(
                model=self.model_name,
                max_tokens_to_sample=int(getattr(self.config, "max_response", 1024)),
                prompt=prompt,
                temperature=float(getattr(self.config, "default_temp", 0.7))
            )
            content = response.completion if hasattr(response, "completion") else None
            self.publish(RequestFinished, request_id, response=content, status="success", usage={})
            if content:
                self.publish(ContentPartFound, request_id, content_part=content)
            self.publish(GenerationFinished, request_id, total_turns=1)
        except Exception as e:
            self.publish(RequestError, request_id, error=str(e), exception=e, traceback=traceback.format_exc())
