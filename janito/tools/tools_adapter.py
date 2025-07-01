from janito.tools.tool_base import ToolBase
from janito.tools.tool_events import ToolCallStarted, ToolCallFinished, ToolCallError
from janito.exceptions import ToolCallException
from janito.tools.tool_base import ToolPermissions

class ToolsAdapterBase:
    """
    Composable entry point for tools management and provisioning in LLM pipelines.
    This class represents an external or plugin-based provider of tool definitions.
    Extend and customize this to load, register, or serve tool implementations dynamically.
    After refactor, also responsible for tool execution.
    """

    def __init__(
        self, tools=None, event_bus=None
    ):
        self._tools = tools or []
        self._event_bus = event_bus  # event bus can be set on all adapters
        self.verbose_tools = False

    def set_verbose_tools(self, value: bool):
        self.verbose_tools = value

    @property
    def event_bus(self):
        return self._event_bus

    @event_bus.setter
    def event_bus(self, bus):
        self._event_bus = bus

    def is_tool_allowed(self, tool):
        """Check if a tool is allowed based on current global AllowedPermissionsState."""
        from janito.tools.permissions import get_global_allowed_permissions
        allowed_permissions = get_global_allowed_permissions()
        perms = tool.permissions  # permissions are mandatory and type-checked
        # If all permissions are False, block all tools
        if not (allowed_permissions.read or allowed_permissions.write or allowed_permissions.execute):
            return False
        for perm in ['read', 'write', 'execute']:
            if getattr(perms, perm) and not getattr(allowed_permissions, perm):
                return False
        return True

    def get_tools(self):
        """Return the list of enabled tools managed by this provider, filtered by allowed permissions."""
        tools = [tool for tool in self._tools if self.is_tool_allowed(tool)]
        return tools

    def set_allowed_permissions(self, allowed_permissions):
        """Set the allowed permissions at runtime. This now updates the global AllowedPermissionsState only."""
        from janito.tools.permissions import set_global_allowed_permissions
        set_global_allowed_permissions(allowed_permissions)

    def add_tool(self, tool):
        self._tools.append(tool)

    def clear_tools(self):
        self._tools = []

    def _validate_arguments_against_schema(self, arguments: dict, schema: dict):
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        missing = [field for field in required if field not in arguments]
        if missing:
            return f"Missing required argument(s): {', '.join(missing)}"
        type_map = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict,
        }
        for key, value in arguments.items():
            if key not in properties:
                continue
            expected_type = properties[key].get("type")
            if expected_type and expected_type in type_map:
                if not isinstance(value, type_map[expected_type]):
                    return f"Argument '{key}' should be of type '{expected_type}', got '{type(value).__name__}'"
        return None

    def execute(self, tool, *args, **kwargs):

        if self.verbose_tools:
            print(
                f"[tools-adapter] [execute] Executing tool: {getattr(tool, 'tool_name', repr(tool))} with args: {args}, kwargs: {kwargs}"
            )
        if isinstance(tool, ToolBase):
            tool.event_bus = self._event_bus
        result = None
        if callable(tool):
            result = tool(*args, **kwargs)
        elif hasattr(tool, "execute") and callable(getattr(tool, "execute")):
            result = tool.execute(*args, **kwargs)
        elif hasattr(tool, "run") and callable(getattr(tool, "run")):
            result = tool.run(*args, **kwargs)
        else:
            raise ValueError("Provided tool is not executable.")

        return result

    def _get_tool_callable(self, tool):
        """Helper to retrieve the primary callable of a tool instance."""
        if callable(tool):
            return tool
        if hasattr(tool, "execute") and callable(getattr(tool, "execute")):
            return getattr(tool, "execute")
        if hasattr(tool, "run") and callable(getattr(tool, "run")):
            return getattr(tool, "run")
        raise ValueError("Provided tool is not executable.")

    def _validate_arguments_against_signature(self, func, arguments: dict):
        """Validate provided arguments against a callable signature.

        Returns an error string if validation fails, otherwise ``None``.
        """
        import inspect

        if arguments is None:
            arguments = {}
        # Ensure the input is a dict to avoid breaking the inspect-based logic
        if not isinstance(arguments, dict):
            return "Tool arguments should be provided as an object / mapping"

        sig = inspect.signature(func)
        params = sig.parameters

        # Check for unexpected arguments (unless **kwargs is accepted)
        accepts_kwargs = any(
            p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values()
        )
        if not accepts_kwargs:
            unexpected = [k for k in arguments.keys() if k not in params]
            if unexpected:
                return (
                    "Unexpected argument(s): " + ", ".join(sorted(unexpected))
                )

        # Check for missing required arguments (ignoring *args / **kwargs / self)
        required_params = [
            name
            for name, p in params.items()
            if p.kind in (
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                inspect.Parameter.KEYWORD_ONLY,
            )
            and p.default is inspect._empty
            and name != "self"
        ]
        missing = [name for name in required_params if name not in arguments]
        if missing:
            return "Missing required argument(s): " + ", ".join(sorted(missing))

        return None

    def execute_by_name(
        self, tool_name: str, *args, request_id=None, arguments=None, **kwargs
    ):
        self._check_tool_permissions(tool_name, request_id, arguments)
        tool = self.get_tool(tool_name)
        self._ensure_tool_exists(tool, tool_name, request_id, arguments)
        func = self._get_tool_callable(tool)

        validation_error = self._validate_tool_arguments(tool, func, arguments, tool_name, request_id)
        if validation_error:
            return validation_error

        # --- SECURITY: Path restriction enforcement ---
        if not getattr(self, 'unrestricted_paths', False):
            workdir = getattr(self, 'workdir', None)
            # Ensure workdir is always set; default to current working directory.
            if not workdir:
                import os
                workdir = os.getcwd()
            from janito.tools.path_security import validate_paths_in_arguments, PathSecurityError
            schema = getattr(tool, 'schema', None)
            try:
                validate_paths_in_arguments(arguments, workdir, schema=schema)
            except PathSecurityError as sec_err:
                # Publish both a ToolCallError and a user-facing ReportEvent for path security errors
                self._publish_tool_call_error(tool_name, request_id, str(sec_err), arguments)
                if self._event_bus:
                    from janito.report_events import ReportEvent, ReportSubtype, ReportAction
                    self._event_bus.publish(
                        ReportEvent(
                            subtype=ReportSubtype.ERROR,
                            message=f"[SECURITY] Path access denied: {sec_err}",
                            action=ReportAction.EXECUTE,
                            tool=tool_name,
                            context={"arguments": arguments, "request_id": request_id}
                        )
                    )
                return f"Security error: {sec_err}"
        # --- END SECURITY ---

        self._publish_tool_call_started(tool_name, request_id, arguments)
        self._print_verbose(f"[tools-adapter] Executing tool: {tool_name} with arguments: {arguments}")
        try:
            result = self.execute(tool, **(arguments or {}), **kwargs)
        except Exception as e:
            self._handle_execution_error(tool_name, request_id, e, arguments)
        self._print_verbose(f"[tools-adapter] Tool execution finished: {tool_name} -> {result}")
        self._publish_tool_call_finished(tool_name, request_id, result)
        return result

    def _validate_tool_arguments(self, tool, func, arguments, tool_name, request_id):
        sig_error = self._validate_arguments_against_signature(func, arguments)
        if sig_error:
            self._publish_tool_call_error(tool_name, request_id, sig_error, arguments)
            return sig_error
        schema = getattr(tool, "schema", None)
        if schema and arguments is not None:
            validation_error = self._validate_arguments_against_schema(arguments, schema)
            if validation_error:
                self._publish_tool_call_error(tool_name, request_id, validation_error, arguments)
                return validation_error
        return None

    def _publish_tool_call_error(self, tool_name, request_id, error, arguments):
        if self._event_bus:
            self._event_bus.publish(
                ToolCallError(
                    tool_name=tool_name,
                    request_id=request_id,
                    error=error,
                    arguments=arguments,
                )
            )

    def _publish_tool_call_started(self, tool_name, request_id, arguments):
        if self._event_bus:
            self._event_bus.publish(
                ToolCallStarted(
                    tool_name=tool_name, request_id=request_id, arguments=arguments
                )
            )

    def _publish_tool_call_finished(self, tool_name, request_id, result):
        if self._event_bus:
            self._event_bus.publish(
                ToolCallFinished(
                    tool_name=tool_name, request_id=request_id, result=result
                )
            )

    def _print_verbose(self, message):
        if self.verbose_tools:
            print(message)

    def execute_function_call_message_part(self, function_call_message_part):
        """
        Execute a FunctionCallMessagePart by extracting the tool name and arguments and dispatching to execute_by_name.
        """
        import json

        function = getattr(function_call_message_part, "function", None)
        tool_call_id = getattr(function_call_message_part, "tool_call_id", None)
        if function is None or not hasattr(function, "name"):
            raise ValueError(
                "FunctionCallMessagePart does not contain a valid function object."
            )
        tool_name = function.name
        arguments = function.arguments
        # Parse arguments if they are a JSON string
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except Exception:
                pass  # Leave as string if not JSON
        if self.verbose_tools:
            print(
                f"[tools-adapter] Executing FunctionCallMessagePart: tool={tool_name}, arguments={arguments}, tool_call_id={tool_call_id}"
            )
        return self.execute_by_name(
            tool_name, request_id=tool_call_id, arguments=arguments
        )

    def _check_tool_permissions(self, tool_name, request_id, arguments):
        # No enabled_tools check anymore; permission checks are handled by is_tool_allowed
        pass

    def _ensure_tool_exists(self, tool, tool_name, request_id, arguments):
        if tool is None:
            error_msg = f"Tool '{tool_name}' not found in registry."
            if self._event_bus:
                self._event_bus.publish(
                    ToolCallError(
                        tool_name=tool_name,
                        request_id=request_id,
                        error=error_msg,
                        arguments=arguments,
                    )
                )
            raise ToolCallException(tool_name, error_msg, arguments=arguments)

    def _handle_execution_error(self, tool_name, request_id, exception, arguments):
        error_msg = f"Exception during execution of tool '{tool_name}': {exception}"
        if self._event_bus:
            self._event_bus.publish(
                ToolCallError(
                    tool_name=tool_name,
                    request_id=request_id,
                    error=error_msg,
                    exception=exception,
                    arguments=arguments,
                )
            )
        raise ToolCallException(
            tool_name, error_msg, arguments=arguments, exception=exception
        )

    def get_tool(self, tool_name):
        """Abstract method: implement in subclass to return tool instance by name"""
        raise NotImplementedError()
