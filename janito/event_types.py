import attr
from typing import Any, ClassVar, Optional, Dict
from enum import Enum
from janito.event_bus.event import Event

class ReportSubtype(Enum):
    INFO = "info"
    ERROR = "error"
    SUCCESS = "success"
    WARNING = "warning"
    STDOUT = "stdout"
    STDERR = "stderr"

class ReportAction(Enum):
    READ = "READ"
    WRITE = "WRITE"
    DELETE = "DELETE"
    UPDATE = "UPDATE"
    EXECUTE = "EXECUTE"
    # Add more as needed

@attr.s(auto_attribs=True, kw_only=True)
class DriverEvent(Event):
    """
    Base class for events related to a driver (e.g., LLM, API provider).
    Includes driver name and request ID for correlation.
    """
    category: ClassVar[str] = "driver"
    driver_name: str
    request_id: str

@attr.s(auto_attribs=True, kw_only=True)
class ToolEvent(Event):
    """
    Base class for events related to tool calls (external or internal tools).
    Includes tool name and request ID for correlation.
    """
    category: ClassVar[str] = "tool"
    tool_name: str
    request_id: str

@attr.s(auto_attribs=True, kw_only=True)
class GenerationStarted(DriverEvent):
    """
    Event indicating that a new content generation process has started.
    'Generation' refers to the process of producing content (e.g., by an LLM) in response to a prompt.
    """
    prompt: Any

@attr.s(auto_attribs=True, kw_only=True)
class GenerationFinished(DriverEvent):
    """
    Event indicating that content generation has finished.
    Contains the original prompt and total number of turns (steps) taken.
    """
    prompt: Any
    total_turns: int

@attr.s(auto_attribs=True, kw_only=True)
class RequestStarted(DriverEvent):
    """
    Event indicating that a request (e.g., API call, user action) has started.
    'Request' refers to any operation sent to a driver or service.
    This event may be emitted multiple times if the system retries a request due to errors or failures before a final response is received.
    """
    payload: Any

@attr.s(auto_attribs=True, kw_only=True)
class RequestFinished(DriverEvent):
    """
    Event indicating that a request has completed.
    Contains the response, duration, and status (e.g., success or failure).
    This event may be emitted multiple times if the system retries a request due to errors or failures before a final response is received.
    """
    response: Any
    duration: float
    status: str
    usage: Any = None

@attr.s(auto_attribs=True, kw_only=True)
class ResponseReceived(DriverEvent):
    """
    Event indicating that a response has been received from a driver or service.
    This event is emitted only after the request has been validated—meaning any necessary retries, error handling, or recovery mechanisms have completed successfully.
    'Response' is the result returned for a request, which may be partial or final.
    """
    response: Any

@attr.s(auto_attribs=True, kw_only=True)
class RequestError(DriverEvent):
    """
    Event indicating that an error occurred during a request.
    Contains error message and exception details.
    This event may be emitted multiple times if the system retries a request due to errors or failures before a final response is received.
    """
    error: str
    exception: Exception

@attr.s(auto_attribs=True, kw_only=True)
class ContentPartFound(DriverEvent):
    """
    Event indicating that a part of the generated content was found or produced.
    Useful for streaming or incremental generation scenarios.
    """
    content_part: Any

@attr.s(auto_attribs=True, kw_only=True)
class ToolCallStarted(ToolEvent):
    """
    Event indicating that a tool call has started.
    Contains the arguments passed to the tool.
    """
    arguments: Any

@attr.s(auto_attribs=True, kw_only=True)
class ToolCallFinished(ToolEvent):
    """
    Event indicating that a tool call has finished.
    Contains the result returned by the tool.
    """
    result: Any

@attr.s(auto_attribs=True, kw_only=True)
class ReportEvent(Event):
    """
    Event for reporting status, errors, warnings, and output.
    Uses enums for subtype and action for type safety and clarity.
    """
    category: ClassVar[str] = "report"
    subtype: ReportSubtype
    message: str
    action: Optional[ReportAction] = None
    tool: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
