import attr
from typing import Any, ClassVar
from janito.event_bus.event import Event

@attr.s(auto_attribs=True, kw_only=True)
class DriverEvent(Event):
    """
    Base class for events related to a driver (e.g., LLM, API provider).
    Includes driver name and request ID for correlation.
    """
    category: ClassVar[str] = "driver"
    driver_name: str = None
    request_id: str = None

@attr.s(auto_attribs=True, kw_only=True)
class GenerationStarted(DriverEvent):
    conversation_history: Any = None

@attr.s(auto_attribs=True, kw_only=True)
class GenerationFinished(DriverEvent):
    total_turns: int = 0

@attr.s(auto_attribs=True, kw_only=True)
class RequestStarted(DriverEvent):
    payload: Any = None

@attr.s(auto_attribs=True, kw_only=True)
class RequestFinished(DriverEvent):
    response: Any = None
    status: str = None
    usage: dict = None

@attr.s(auto_attribs=True, kw_only=True)
class RequestError(DriverEvent):
    error: str = None
    exception: Exception = None
    traceback: str = None

@attr.s(auto_attribs=True, kw_only=True)
class EmptyResponseEvent(DriverEvent):
    error: str = None
    exception: Exception = None
    traceback: str = None
    details: dict = None

@attr.s(auto_attribs=True, kw_only=True)
class ContentPartFound(DriverEvent):
    content_part: Any = None

@attr.s(auto_attribs=True, kw_only=True)
class ToolCallStarted(DriverEvent):
    tool_call_id: str = None
    name: str = None
    arguments: Any = None
    @property
    def tool_name(self):
        return self.name

@attr.s(auto_attribs=True, kw_only=True)
class ToolCallFinished(DriverEvent):
    tool_call_id: str = None
    name: str = None
    result: Any = None
    @property
    def tool_name(self):
        return self.name

@attr.s(auto_attribs=True, kw_only=True)
class ResponseReceived(DriverEvent):
    parts: list = None
    tool_results: list = None  # each as dict or custom ToolResult dataclass
    timestamp: float = None  # UNIX epoch seconds, normalized
    metadata: dict = None
