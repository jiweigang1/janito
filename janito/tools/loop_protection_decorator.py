import functools
import time
import threading
from typing import Callable, Any
from janito.tools.loop_protection import LoopProtection
from janito.tools.tool_use_tracker import normalize_path


# Global tracking for decorator-based loop protection
_decorator_call_tracker = {}
_decorator_call_tracker_lock = threading.Lock()


def protect_against_loops(
    max_calls: int = 5,
    time_window: float = 10.0
):
    """
    Decorator that adds loop protection to tool run methods.
    
    This decorator monitors tool executions and prevents excessive calls within
    a configurable time window. It helps prevent infinite loops or excessive
    resource consumption when tools are called repeatedly.
    
    When the configured limits are exceeded, the decorator raises a RuntimeError
    with a descriptive message. This exception will propagate up the call stack
    unless caught by a try/except block in the calling code.
    
    The decorator works by:
    1. Tracking the number of calls to the decorated function
    2. Checking if the calls exceed the configured limits
    3. Raising a RuntimeError if a potential loop is detected
    4. Allowing the method to proceed normally if the operation is safe
    
    Args:
        max_calls (int): Maximum number of calls allowed within the time window.
                        Defaults to 5 calls.
        time_window (float): Time window in seconds for detecting excessive calls.
                            Defaults to 10.0 seconds.
                              
    Example:
        >>> @protect_against_loops(max_calls=3, time_window=5.0)
        >>> def run(self, path: str) -> str:
        >>>     # Implementation here
        >>>     pass
          
        >>> @protect_against_loops(max_calls=10, time_window=30.0)
        >>> def run(self, file_paths: list) -> str:
        >>>     # Implementation here
        >>>     pass
        
    Note:
        When loop protection is triggered, a RuntimeError will be raised with a
        descriptive message. This exception will propagate up the call stack
        unless caught by a try/except block in the calling code.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get the tool instance (self)
            if not args:
                # This shouldn't happen in normal usage as methods need self
                return func(*args, **kwargs)
            
            # Use the function name as the operation name
            op_name = func.__name__
            
            # Check call limits
            current_time = time.time()
            
            with _decorator_call_tracker_lock:
                # Clean up old entries outside the time window
                if op_name in _decorator_call_tracker:
                    _decorator_call_tracker[op_name] = [
                        timestamp for timestamp in _decorator_call_tracker[op_name]
                        if current_time - timestamp <= time_window
                    ]
                
                # Check if we're exceeding the limit
                if op_name in _decorator_call_tracker:
                    if len(_decorator_call_tracker[op_name]) >= max_calls:
                        # Check if all recent calls are within the time window
                        if all(current_time - timestamp <= time_window 
                              for timestamp in _decorator_call_tracker[op_name]):
                            # Define the error reporting function
                            def _report_error_and_raise(args, operation_type):
                                # Get the tool instance to access report_error method if available
                                tool_instance = args[0] if args else None
                                error_msg = f"Loop protection: Too many {operation_type} operations in a short time period ({max_calls} calls in {time_window}s)"
                                
                                # Try to report the error through the tool's reporting mechanism
                                if hasattr(tool_instance, 'report_error'):
                                    try:
                                        tool_instance.report_error(error_msg)
                                    except Exception:
                                        pass  # If reporting fails, we still raise the error
                                
                                raise RuntimeError(error_msg)
                            
                            _report_error_and_raise(args, op_name)
                
                # Record this call
                if op_name not in _decorator_call_tracker:
                    _decorator_call_tracker[op_name] = []
                _decorator_call_tracker[op_name].append(current_time)
            
            # Proceed with the original function
            return func(*args, **kwargs)
        return wrapper
    return decorator