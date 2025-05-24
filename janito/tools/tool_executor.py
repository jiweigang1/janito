from janito.tools.adapters.local.adapter import LocalToolsAdapter
from janito.tools.tool_events import ToolCallStarted, ToolCallFinished, ToolCallError
from janito.tools.tool_base import ToolBase
from janito.exceptions import ToolCallException

class ToolExecutor:
    """
    Responsible for executing tools (functions, scripts, etc.) within the janito framework.
    Handles input, output, and error management for tool execution.
    Integrates with LocalToolsAdapter to resolve and execute tools by name.
    Emits events for tool execution lifecycle using the provided event_bus (must be explicitly passed).
    Optionally enforces a per-executor allow-list (allowed_tools), restricting which tool names can be executed:
      - If allowed_tools is not None, only tool names present in this list can be executed; others are rejected.
    """

    """
    Responsible for executing tools (functions, scripts, etc.) within the janito framework.
    Handles input, output, and error management for tool execution.
    Integrates with LocalToolsAdapter to resolve and execute tools by name.
    Emits events for tool execution lifecycle using the provided event_bus (must be explicitly passed).
    """
    def __init__(self, registry: LocalToolsAdapter = None, event_bus=None, allowed_tools: list = None):
        if event_bus is None:
            raise ValueError("ToolExecutor requires an event_bus to be provided.")
        self.registry = registry or LocalToolsAdapter()
        self._event_bus = event_bus
        self._allowed_tools = set(allowed_tools) if allowed_tools is not None else None

    @property
    def event_bus(self):
        return self._event_bus

    @event_bus.setter
    def event_bus(self, bus):
        if bus is None:
            raise ValueError("ToolExecutor requires a non-None event_bus.")
        self._event_bus = bus

    def _validate_arguments_against_schema(self, arguments: dict, schema: dict):
        """
        Validate arguments against the provided JSON schema (OpenAI-compatible).
        Checks required fields and basic type validation.
        Returns error message if validation fails, else None.
        """
        properties = schema.get('properties', {})
        required = schema.get('required', [])
        # Check required fields
        missing = [field for field in required if field not in arguments]
        if missing:
            return f"Missing required argument(s): {', '.join(missing)}"
        # Type validation
        type_map = {
            'string': str,
            'integer': int,
            'number': (int, float),
            'boolean': bool,
            'array': list,
            'object': dict,
        }
        for key, value in arguments.items():
            if key not in properties:
                continue  # Ignore extra fields
            expected_type = properties[key].get('type')
            if expected_type and expected_type in type_map:
                if not isinstance(value, type_map[expected_type]):
                    return f"Argument '{key}' should be of type '{expected_type}', got '{type(value).__name__}'"
        # Optionally: add more checks (enums, min/max, etc.) here
        return None

    def execute(self, tool, *args, **kwargs):
        # If the tool is a ToolBase instance, propagate the event bus
        if isinstance(tool, ToolBase):
            tool.event_bus = self._event_bus
        if callable(tool):
            return tool(*args, **kwargs)
        elif hasattr(tool, 'execute') and callable(getattr(tool, 'execute')):
            return tool.execute(*args, **kwargs)
        elif hasattr(tool, 'run') and callable(getattr(tool, 'run')):
            return tool.run(*args, **kwargs)
        else:
            raise ValueError("Provided tool is not executable.")

    def execute_by_name(self, tool_name: str, *args, request_id=None, arguments=None, **kwargs):
        # Restrict execution to allowed tools if enforced
        if self._allowed_tools is not None and tool_name not in self._allowed_tools:
            error_msg = f"Tool '{tool_name}' is not permitted by executor allow-list."
            self._event_bus.publish(ToolCallError(tool_name=tool_name, request_id=request_id, error=error_msg, arguments=arguments))
            raise ToolCallException(tool_name, error_msg, arguments=arguments)

        tool = self.registry.get_tool(tool_name)
        if tool is None:
            error_msg = f"Tool '{tool_name}' not found in registry."
            self._event_bus.publish(ToolCallError(tool_name=tool_name, request_id=request_id, error=error_msg, arguments=arguments))
            raise ToolCallException(tool_name, error_msg, arguments=arguments)
        # Schema-based validation before execution
        schema = getattr(tool, 'schema', None)
        if schema and arguments is not None:
            validation_error = self._validate_arguments_against_schema(arguments, schema)
            if validation_error:
                self._event_bus.publish(ToolCallError(tool_name=tool_name, request_id=request_id, error=validation_error, arguments=arguments))
                return validation_error
        self._event_bus.publish(ToolCallStarted(tool_name=tool_name, request_id=request_id, arguments=arguments))
        try:
            result = self.execute(tool, *(arguments or []), **kwargs)
        except Exception as e:
            error_msg = f"Exception during execution of tool '{tool_name}': {e}"
            self._event_bus.publish(ToolCallError(tool_name=tool_name, request_id=request_id, error=error_msg, exception=e, arguments=arguments))
            raise ToolCallException(tool_name, error_msg, arguments=arguments, exception=e)
        self._event_bus.publish(ToolCallFinished(tool_name=tool_name, request_id=request_id, result=result))
        return result
