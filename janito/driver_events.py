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
    driver_name: str
    request_id: str

@attr.s(auto_attribs=True, kw_only=True)
class GenerationStarted(DriverEvent):
    """
    Event indicating that a new content generation process has started.
    'Generation' refers to the process of producing content (e.g., by an LLM) in response to a prompt.
    """
    conversation_history: Any

@attr.s(auto_attribs=True, kw_only=True)
class GenerationFinished(DriverEvent):
    """
    Event indicating that content generation has finished.
    Contains the total number of turns (steps) taken.
    """
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
    Contains the response and status (e.g., success or failure).
    This event may be emitted multiple times if the system retries a request due to errors or failures before a final response is received.
    """
    response: Any
    status: str
    usage: dict = None

@attr.s(auto_attribs=True, kw_only=True)
class RequestError(DriverEvent):
    """
    Event indicating that an error occurred during a request.
    Contains error message and exception details.
    This event may be emitted multiple times if the system retries a request due to errors or failures before a final response is received.
    """
    error: str
    exception: Exception
    traceback: str = None

@attr.s(auto_attribs=True, kw_only=True)
class EmptyResponseEvent(DriverEvent):
    """
    Event indicating that an empty response was received from an LLM or API provider.
    Used for signaling that no content or candidates were returned where some were expected,
    which may indicate a model or infrastructure issue.
    """
    error: str = None
    exception: Exception = None
    traceback: str = None
    details: dict = None

@attr.s(auto_attribs=True, kw_only=True)
class ContentPartFound(DriverEvent):
    """
    Event indicating that a part of the generated content was found or produced.
    Useful for streaming or incremental generation scenarios.
    """
    content_part: Any

@attr.s(auto_attribs=True, kw_only=True)
class ToolCallStarted(DriverEvent):
    """
    Event indicating that a tool/function call has started.
    """
    tool_call_id: str
    name: str
    arguments: Any

@attr.s(auto_attribs=True, kw_only=True)
class ToolCallFinished(DriverEvent):
    """
    Event indicating that a tool/function call has finished and returned a result.
    """
    tool_call_id: str
    name: str
    result: Any

@attr.s(auto_attribs=True, kw_only=True)
class ResponseReceived(DriverEvent):
    """
    Aggregate event emitted by a driver after an LLM request completes.

    Fields:
      - content_parts: list of generated content strings for the user.
      - tool_calls: list of tool call objects (dicts or ToolCall dataclass instances) that the LLM requests be run.
      - tool_results: list of tool result objects, filled by the agent (optional, not set by the driver).
      - timestamp: float, normalized UNIX epoch seconds (from the LLM API or system clock).
      - metadata: dict for any other details, e.g. usage, raw API response data, etc.

    The agent inspects tool_calls, runs tools if present, and updates conversation history as needed. Responses with no tool_calls are "final" turns to be shown to the user.
    """
    content_parts: list
    tool_calls: list  # each as dict or custom ToolCall dataclass
    tool_results: list = None  # each as dict or custom ToolResult dataclass
    timestamp: float = None  # UNIX epoch seconds, normalized
    metadata: dict = None
