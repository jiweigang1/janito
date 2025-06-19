class ToolCallException(Exception):
    """
    Exception raised when a tool call fails (e.g., not found, invalid arguments, invocation failure).
    This is distinct from ToolCallError event, which is for event bus notification.
    """

    def __init__(self, tool_name, error, arguments=None, exception=None):
        self.tool_name = tool_name
        self.error = error
        self.arguments = arguments
        self.original_exception = exception
        super().__init__(f"ToolCallException: {tool_name}: {error}")


class MissingProviderSelectionException(Exception):
    """
    Raised when no provider is specified and no default provider is set.
    """

    def __init__(self, configured=None, supported=None):
        self.configured = configured or []
        self.supported = supported or []
        super().__init__("No provider specified and no default provider is set.")
