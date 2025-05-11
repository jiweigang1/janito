import pytest
from janito.event_bus.bus import EventBus
from janito.event_types import (
    RequestStarted, RequestFinished, ResponseReceived, RequestError,
    ToolCallStarted, ToolCallFinished
)

class HandlerRecorder:
    def __init__(self):
        self.events = []
    def __call__(self, event):
        self.events.append(event)

def test_event_bus_pub_sub():
    bus = EventBus()
    handler_started = HandlerRecorder()
    handler_finished = HandlerRecorder()

    bus.subscribe(RequestStarted, handler_started)
    bus.subscribe(RequestFinished, handler_finished)

    event1 = RequestStarted('driver1', {'prompt': 'hi'}, 'req-1')
    event2 = RequestFinished('driver1', {'result': 'ok'}, 'req-1', 0.5, 'success')

    bus.publish(event1)
    bus.publish(event2)

    assert handler_started.events == [event1]
    assert handler_finished.events == [event2]

def test_event_bus_unsubscribe():
    bus = EventBus()
    handler = HandlerRecorder()
    bus.subscribe(RequestError, handler)
    event = RequestError('driver1', 'error', 'req-2', Exception('fail'))
    bus.publish(event)
    assert handler.events == [event]
    bus.unsubscribe(RequestError, handler)
    bus.publish(event)
    assert handler.events == [event]  # Should not be called again
