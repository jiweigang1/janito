import inspect
from .bus import event_bus

class EventHandlerBase:
    """
    Base class for event handler classes.
    Automatically subscribes methods named on_<EventClassName> to the event bus for the corresponding event type.
    Pass the event module (e.g., janito.event_types) to the constructor.
    """
    def __init__(self, event_module):
        for name, method in inspect.getmembers(self, predicate=inspect.ismethod):
            if name.startswith("on_"):
                event_class_name = name[3:]
                event_class = getattr(event_module, event_class_name, None)
                if event_class:
                    event_bus.subscribe(event_class, method)
