import pytest
from janito.event_bus.bus import EventBus
from janito.driver_events import RequestStarted, RequestFinished, ResponseReceived, RequestError
from janito.tool_events import ToolCallStarted, ToolCallFinished
from janito.utils import kwargs_from_locals

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

    driver_name = 'driver1'
    request_id = 'req-1'
    payload = {'prompt': 'hi'}
    event1 = RequestStarted(**kwargs_from_locals('driver_name', 'request_id', 'payload'))
    response = {'result': 'ok'}
    duration = 0.5
    status = 'success'
    event2 = RequestFinished(**kwargs_from_locals('driver_name', 'request_id', 'response', 'duration', 'status'))

    bus.publish(event1)
    bus.publish(event2)

    assert handler_started.events == [event1]
    assert handler_finished.events == [event2]

def test_event_bus_unsubscribe():
    bus = EventBus()
    handler = HandlerRecorder()
    bus.subscribe(RequestError, handler)
    driver_name = 'driver1'
    request_id = 'req-2'
    error = 'error'
    exception = Exception('fail')
    event = RequestError(**kwargs_from_locals('driver_name', 'request_id', 'error', 'exception'))
    bus.publish(event)
    assert handler.events == [event]
    bus.unsubscribe(RequestError, handler)
    bus.publish(event)
    assert handler.events == [event]  # Should not be called again
