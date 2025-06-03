from janito.tools.tool_base import ToolBase
from janito.tools.tool_events import ToolCallStarted, ToolCallFinished, ToolCallError
from janito.exceptions import ToolCallException
from typing import Optional

class ToolsAdapterBase:
    """
    Composable entry point for tools management and provisioning in LLM pipelines.
    This class represents an external or plugin-based provider of tool definitions.
    Extend and customize this to load, register, or serve tool implementations dynamically.
    After refactor, also responsible for tool execution.
    """
    def __init__(self, tools=None, event_bus=None, allowed_tools: Optional[list]=None):
        self._tools = tools or []
        self._event_bus = event_bus  # event bus can be set on all adapters
        self._allowed_tools = set(allowed_tools) if allowed_tools is not None else None
        self.verbose_tools = False

    def set_verbose_tools(self, value: bool):
        self.verbose_tools = value

    @property
    def event_bus(self):
        return self._event_bus

    @event_bus.setter
    def event_bus(self, bus):
        self._event_bus = bus

    def get_tools(self):
        """Return the list of tools managed by this provider."""
        return self._tools

    def add_tool(self, tool):
        self._tools.append(tool)

    def clear_tools(self):
        self._tools = []

    def _validate_arguments_against_schema(self, arguments: dict, schema: dict):
        properties = schema.get('properties', {})
        required = schema.get('required', [])
        missing = [field for field in required if field not in arguments]
        if missing:
            return f"Missing required argument(s): {', '.join(missing)}"
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
                continue
            expected_type = properties[key].get('type')
            if expected_type and expected_type in type_map:
                if not isinstance(value, type_map[expected_type]):
                    return f"Argument '{key}' should be of type '{expected_type}', got '{type(value).__name__}'"
        return None

    def execute(self, tool, *args, **kwargs):
        
        if self.verbose_tools:
            print(f"[tools-adapter] [execute] Executing tool: {getattr(tool, 'tool_name', repr(tool))} with args: {args}, kwargs: {kwargs}")
        if isinstance(tool, ToolBase):
            tool.event_bus = self._event_bus
        result = None
        if callable(tool):
            result = tool(*args, **kwargs)
        elif hasattr(tool, 'execute') and callable(getattr(tool, 'execute')):
            result = tool.execute(*args, **kwargs)
        elif hasattr(tool, 'run') and callable(getattr(tool, 'run')):
            result = tool.run(*args, **kwargs)
        else:
            raise ValueError("Provided tool is not executable.")

        return result

    def execute_by_name(self, tool_name: str, *args, request_id=None, arguments=None, **kwargs):
        self._check_tool_permissions(tool_name, request_id, arguments)
        tool = self.get_tool(tool_name)
        self._ensure_tool_exists(tool, tool_name, request_id, arguments)
        schema = getattr(tool, 'schema', None)
        if schema and arguments is not None:
            validation_error = self._validate_arguments_against_schema(arguments, schema)
            if validation_error:
                if self._event_bus:
                    self._event_bus.publish(ToolCallError(tool_name=tool_name, request_id=request_id, error=validation_error, arguments=arguments))
                return validation_error
        if self.verbose_tools:
            print(f"[tools-adapter] Executing tool: {tool_name} with arguments: {arguments}")
        if self._event_bus:
            self._event_bus.publish(ToolCallStarted(tool_name=tool_name, request_id=request_id, arguments=arguments))
        try:
            result = self.execute(tool, **(arguments or {}), **kwargs)
        except Exception as e:
            self._handle_execution_error(tool_name, request_id, e, arguments)
        if self.verbose_tools:
            print(f"[tools-adapter] Tool execution finished: {tool_name} -> {result}")
        if self._event_bus:
            self._event_bus.publish(ToolCallFinished(tool_name=tool_name, request_id=request_id, result=result))
        return result

    def execute_function_call_message_part(self, function_call_message_part):
        """
        Execute a FunctionCallMessagePart by extracting the tool name and arguments and dispatching to execute_by_name.
        """
        import json
        function = getattr(function_call_message_part, 'function', None)
        tool_call_id = getattr(function_call_message_part, 'tool_call_id', None)
        if function is None or not hasattr(function, 'name'):
            raise ValueError("FunctionCallMessagePart does not contain a valid function object.")
        tool_name = function.name
        arguments = function.arguments
        # Parse arguments if they are a JSON string
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except Exception:
                pass  # Leave as string if not JSON
        if self.verbose_tools:
            print(f"[tools-adapter] Executing FunctionCallMessagePart: tool={tool_name}, arguments={arguments}, tool_call_id={tool_call_id}")
        return self.execute_by_name(tool_name, request_id=tool_call_id, arguments=arguments)

    def _check_tool_permissions(self, tool_name, request_id, arguments):
        if self._allowed_tools is not None and tool_name not in self._allowed_tools:
            error_msg = f"Tool '{tool_name}' is not permitted by adapter allow-list."
            if self._event_bus:
                self._event_bus.publish(ToolCallError(tool_name=tool_name, request_id=request_id, error=error_msg, arguments=arguments))
            raise ToolCallException(tool_name, error_msg, arguments=arguments)

    def _ensure_tool_exists(self, tool, tool_name, request_id, arguments):
        if tool is None:
            error_msg = f"Tool '{tool_name}' not found in registry."
            if self._event_bus:
                self._event_bus.publish(ToolCallError(tool_name=tool_name, request_id=request_id, error=error_msg, arguments=arguments))
            raise ToolCallException(tool_name, error_msg, arguments=arguments)

    def _handle_execution_error(self, tool_name, request_id, exception, arguments):
        error_msg = f"Exception during execution of tool '{tool_name}': {exception}"
        if self._event_bus:
            self._event_bus.publish(ToolCallError(tool_name=tool_name, request_id=request_id, error=error_msg, exception=exception, arguments=arguments))
        raise ToolCallException(tool_name, error_msg, arguments=arguments, exception=exception)

    def get_tool(self, tool_name):
        """Abstract method: implement in subclass to return tool instance by name"""
        raise NotImplementedError()
