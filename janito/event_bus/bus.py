from collections import defaultdict
from datetime import datetime

class EventBus:
    """
    Generic event bus for publish/subscribe event-driven communication.
    Automatically injects a timestamp (event.timestamp) into each event when published.
    """
    def __init__(self):
        self._subscribers = defaultdict(list)

    def subscribe(self, event_type, callback):
        """Subscribe a callback to a specific event type."""
        self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type, callback):
        """Unsubscribe a callback from a specific event type."""
        if callback in self._subscribers[event_type]:
            self._subscribers[event_type].remove(callback)

    def publish(self, event):
        """
        Publish an event to all relevant subscribers.
        """
        for event_type, callbacks in self._subscribers.items():
            if isinstance(event, event_type):
                for callback in callbacks:
                    callback(event)

# Singleton instance for global use
event_bus = EventBus()
