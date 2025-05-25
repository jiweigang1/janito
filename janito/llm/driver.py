import threading
from abc import ABC, abstractmethod
from queue import Queue
from janito.llm.driver_input import DriverInput

class LLMDriver(ABC):
    """
    Abstract base class for LLM drivers (threaded, queue-based).
    Subclasses must implement _process_input to process a DriverInput and emit events to the output queue.

    Workflow:
      - Accept DriverInput via input_queue.
      - Put DriverEvents on output_queue.
      - Use start() to launch worker loop in a thread.
    """

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
                self._process_input(driver_input)
            except Exception as e:
                # Should emit a RequestError via output_queue if needed
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

    @abstractmethod
    def _process_input(self, driver_input: DriverInput):
        """Implement: Use driver_input (config, conversation_history, tool_schema) to call provider, yield driver events, etc."""
        pass
