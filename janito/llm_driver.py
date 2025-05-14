from abc import ABC, abstractmethod
from typing import Optional
import threading
import queue
from janito.tool_registry import ToolRegistry
from janito.conversation_history import LLMConversationHistory

class LLMDriver(ABC):
    """
    Abstract base class for LLM drivers. Each driver represents a specific model or capability within a provider.
    Implements the streaming event-driven interface (stream_generate) with built-in threading, queueing, and event bus logic.
    Subclasses must implement the provider-specific _run_generation method.
    """
    def __init__(self, provider_name: str, model_name: str, api_key: str, tool_registry: ToolRegistry = None):
        self.provider_name = provider_name
        self.model_name = model_name
        self.api_key = api_key
        self.tool_registry = tool_registry or ToolRegistry()
        self.event_bus = None
        self.cancel_event = None

    def stream_generate(self, conversation_history: LLMConversationHistory, system_prompt: Optional[str] = None, tools: Optional[list] = None, **kwargs):
        """
        Stream generation events from the LLM driver in a thread-safe, cancellable manner.
        This method starts the generation process in a background thread, emits events to a thread-safe queue,
        and yields these events to the caller as they are produced.
        Subclasses should implement _run_generation(conversation_history, system_prompt, tools, **kwargs).
        Args:
            conversation_history (LLMConversationHistory): The full conversation history object.
            system_prompt (Optional[str]): An optional system prompt.
            tools (Optional[list]): Optional list of tools/functions.
            **kwargs: Additional driver-specific parameters.
        """
        event_queue = queue.Queue()
        cancel_event = kwargs.pop('cancel_event', None)
        if cancel_event is None:
            cancel_event = threading.Event()
        self.cancel_event = cancel_event
        def event_bus_publish(event):
            event_queue.put(event)
        class QueueEventBus:
            def publish(self, event):
                event_bus_publish(event)
        self.event_bus = QueueEventBus()
        def generation_thread():
            try:
                self._run_generation(conversation_history, system_prompt, tools, **kwargs)
            except Exception as exc:
                import traceback
                tb_str = traceback.format_exc()
                event_queue.put({'type': 'exception', 'exception': exc, 'traceback': tb_str})
            finally:
                event_queue.put(None)  # Use None as the sentinel
                self.event_bus = None
                self.cancel_event = None
        thread = threading.Thread(target=generation_thread, daemon=True)
        thread.start()
        while True:
            event = event_queue.get()
            if event is None:
                break
            yield event

    def publish(self, event_type, request_id, **kwargs):
        """
        Publish an event of the given type with common driver/request info and extra args.
        Args:
            event_type: The event class/type to instantiate.
            request_id: The request ID for correlation.
            **kwargs: Additional event-specific arguments.
        """
        event = event_type(driver_name=self.get_name(), request_id=request_id, **kwargs)
        if self.event_bus is not None:
            self.event_bus.publish(event)

    @abstractmethod
    def _run_generation(self, conversation_history: LLMConversationHistory, system_prompt: Optional[str], tools: Optional[list], **kwargs):
        """
        Provider-specific generation logic. Subclasses must implement this method.
        Args:
            conversation_history (LLMConversationHistory): The full conversation history object.
            system_prompt (Optional[str]): An optional system prompt.
            tools (Optional[list]): Optional list of tools/functions.
            **kwargs: Additional driver-specific parameters.
        """
        pass

    def get_name(self) -> str:
        """
        Return the full name of the driver in the format provider_name/model_name.
        Returns:
            str: The driver name.
        """
        return f"{self.provider_name}/{self.model_name}"
