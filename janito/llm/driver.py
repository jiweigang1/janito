import threading
from abc import ABC, abstractmethod
from queue import Queue
from janito.llm.driver_input import DriverInput
from janito.driver_events import RequestStarted, RequestError, ResponseReceived

class LLMDriver(ABC):
    """
    Abstract base class for LLM drivers (threaded, queue-based).
    Subclasses must implement _call_api and _convert_completion_message_to_parts.
    Workflow:
      - Accept DriverInput via input_queue.
      - Put DriverEvents on output_queue.
      - Use start() to launch worker loop in a thread.
    """

    available = True
    unavailable_reason = None

    def __init__(self, input_queue: Queue, output_queue: Queue):
        self.input_queue = input_queue
        self.output_queue = output_queue
        self._thread = None

    def start(self):
        """Launch the driver's background thread to process DriverInput objects."""
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        while True:
            driver_input = self.input_queue.get()
            try:
                self.process_input(driver_input)
            except Exception as e:
                from janito.driver_events import RequestError
                import traceback
                self.output_queue.put(
                    RequestError(
                        driver_name=self.__class__.__name__,
                        request_id=getattr(driver_input.config, 'request_id', None),
                        error=str(e),
                        exception=e,
                        traceback=traceback.format_exc()
                    )
                )

    def handle_driver_unavailable(self, request_id):
        self.output_queue.put(RequestError(
            driver_name=self.__class__.__name__,
            request_id=request_id,
            error=self.unavailable_reason,
            exception=ImportError(self.unavailable_reason),
            traceback=None
        ))

    def emit_response_received(self, driver_name, request_id, result, parts, timestamp=None, metadata=None):
        self.output_queue.put(ResponseReceived(
            driver_name=driver_name,
            request_id=request_id,
            parts=parts,
            tool_results=[],
            timestamp=timestamp,
            metadata=metadata or {}
        ))

    def process_input(self, driver_input: DriverInput):
        config = driver_input.config
        request_id = getattr(config, 'request_id', None)
        if not self.available:
            self.handle_driver_unavailable(request_id)
            return
        self.output_queue.put(RequestStarted(driver_name=self.__class__.__name__, request_id=request_id, payload={}))
        try:
            result = self._call_api(driver_input)
            message = self._get_message_from_result(result)
            parts = self._convert_completion_message_to_parts(message) if message else []
            timestamp = getattr(result, 'created', None)
            metadata = {"usage": getattr(result, 'usage', None), "raw_response": result}
            self.emit_response_received(self.__class__.__name__, request_id, result, parts, timestamp, metadata)
        except Exception as ex:
            import traceback
            self.output_queue.put(RequestError(
                driver_name=self.__class__.__name__,
                request_id=request_id,
                error=str(ex),
                exception=ex,
                traceback=traceback.format_exc()
            ))

    @abstractmethod
    def _call_api(self, driver_input: DriverInput):
        """Subclasses implement: Use driver_input to call provider and return result object."""
        pass

    @abstractmethod
    def _convert_completion_message_to_parts(self, message):
        """Subclasses implement: Convert provider message to list of MessagePart objects."""
        pass

    def _get_message_from_result(self, result):
        """Extract the message object from the provider result. Subclasses may override if needed."""
        if hasattr(result, 'choices') and result.choices:
            return result.choices[0].message
        return None
