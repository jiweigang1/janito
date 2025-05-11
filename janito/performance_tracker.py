from datetime import timedelta
from janito.event_bus.handler import EventHandlerBase
import janito.event_types as driver_events

class PerformanceTracker(EventHandlerBase):
    """
    Tracks performance metrics (timing, etc.) for LLM driver requests using the event bus.
    Now also provides token usage statistics for the last event.
    """
    def __init__(self):
        self._events = []
        self._active_requests = {}
        super().__init__(driver_events)

    def on_RequestStarted(self, event):
        self._active_requests[event.request_id] = {
            'driver_name': event.driver_name,
            'start_time': event.timestamp,
            'payload': event.payload
        }

    def on_RequestFinished(self, event):
        req = self._active_requests.pop(event.request_id, None)
        if req:
            end_time = req['start_time'] + timedelta(seconds=event.duration) if hasattr(event, 'duration') else None
            record = {
                'driver_name': req['driver_name'],
                'request_id': event.request_id,
                'start_time': req['start_time'],
                'end_time': end_time,
                'duration': event.duration,
                'status': event.status,
                'response': event.response
            }
            self._events.append(record)

    def get_all_events(self):
        return list(self._events)

    def get_last_token_usage(self):
        """
        Returns a normalized dict with keys: total_tokens, prompt_tokens, completion_tokens.
        Works for both OpenAI (total_tokens, prompt_tokens, completion_tokens) and Gemini (total_token_count, prompt_token_count, candidates_token_count).
        If a value is missing, it is set to 0.
        """
        if not self._events:
            return {"total_tokens": 0, "prompt_tokens": 0, "completion_tokens": 0}
        last_event = self._events[-1]
        response = last_event.get('response', {})
        usage = None
        # Try to extract usage dict from response
        if hasattr(response, 'usage'):
            usage = getattr(response, 'usage', {})
        elif isinstance(response, dict) and 'usage' in response:
            usage = response['usage']
        else:
            usage = {}
        result = {"total_tokens": 0, "prompt_tokens": 0, "completion_tokens": 0}
        if isinstance(usage, dict):
            # OpenAI format
            if any(k in usage for k in ("total_tokens", "prompt_tokens", "completion_tokens")):
                result["total_tokens"] = usage.get("total_tokens", 0)
                result["prompt_tokens"] = usage.get("prompt_tokens", 0)
                result["completion_tokens"] = usage.get("completion_tokens", 0)
            # Gemini format
            elif any(k in usage for k in ("total_token_count", "prompt_token_count", "candidates_token_count")):
                result["total_tokens"] = usage.get("total_token_count", 0)
                result["prompt_tokens"] = usage.get("prompt_token_count", 0)
                result["completion_tokens"] = usage.get("candidates_token_count", 0)
        return result
