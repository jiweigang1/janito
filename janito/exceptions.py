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
