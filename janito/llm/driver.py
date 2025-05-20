from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Union
import threading
import queue
from janito.tool_registry import ToolRegistry

class LLMDriver(ABC):
    """
    Abstract base class for LLM drivers. Each driver represents a specific model or capability within a provider.
    Now manages its own conversation history internally. The generate/stream_generate method accepts either a list of messages or a prompt.
    Implements the streaming event-driven interface (stream_generate) with built-in threading, queueing, and event bus logic.
    Subclasses must implement the provider-specific _run_generation method.
    """
    def __init__(self, name: str, model_name: str, api_key: str, tool_registry: ToolRegistry = None):
        self.name = name
        self.model_name = model_name
        self.api_key = api_key
        self.tool_registry = tool_registry or ToolRegistry()
        self.event_bus = None
        self.cancel_event = None
        self._history: List[Dict[str, Any]] = []  # Internal conversation history

    @property
    def model_name(self):
        # Always return the canonical model name for the driver
        return getattr(self, '_model_name', getattr(self, 'model', None))

    @model_name.setter
    def model_name(self, value):
        self._model_name = value

    def stream_generate(self, messages_or_prompt: Union[List[Dict[str, Any]], str], system_prompt: Optional[str] = None, tools: Optional[list] = None, **kwargs):
        """
        Stream generation events from the LLM driver in a thread-safe, cancellable manner.
        Accepts either a list of messages or a prompt string. Manages conversation history internally.
        This method starts the generation process in a background thread, emits events to a thread-safe queue,
        and yields these events to the caller as they are produced.
        Subclasses should implement _run_generation(messages_or_prompt, system_prompt, tools, **kwargs).
        Args:
            messages_or_prompt (Union[List[Dict], str]): The conversation as a list of messages or a prompt string.
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
                self._run_generation(messages_or_prompt, system_prompt, tools, **kwargs)
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
            try:
                event = event_queue.get(timeout=0.1)
            except queue.Empty:
                continue
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
    def _run_generation(self, messages_or_prompt: Union[List[Dict[str, Any]], str], system_prompt: Optional[str], tools: Optional[list], **kwargs):
        """
        Provider-specific generation logic. Subclasses must implement this method.
        Args:
            messages_or_prompt (Union[List[Dict], str]): The conversation as a list of messages or a prompt string.
            system_prompt (Optional[str]): An optional system prompt.
            tools (Optional[list]): Optional list of tools/functions.
            **kwargs: Additional driver-specific parameters.
        """
        pass

    def get_name(self) -> str:
        """
        Return the full name of the driver in the format name/model_name.
        Returns:
            str: The driver name.
        """
        return f"{self.name}/{self.model_name}"

    def get_history(self) -> List[Dict[str, Any]]:
        """
        Get the internal conversation history.
        """
        return list(self._history)

    def clear_history(self):
        """
        Clear the internal conversation history.
        """
        self._history.clear()
