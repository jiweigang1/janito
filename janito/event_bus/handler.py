import inspect
from .bus import event_bus

class EventHandlerBase:
    """
    Base class for event handler classes.
    Automatically subscribes methods named on_<EventClassName> to the event bus for the corresponding event type.
    Pass one or more event modules (e.g., janito.report_events, janito.driver_events) to the constructor.
    """
    def __init__(self, *event_modules):
        for name, method in inspect.getmembers(self, predicate=inspect.ismethod):
            if name.startswith("on_"):
                event_class_name = name[3:]
                event_class = None
                for module in event_modules:
                    event_class = getattr(module, event_class_name, None)
                    if event_class:
                        if event_class_name == 'ReportEvent':
                            pass
                        break
                if event_class:
                    event_bus.subscribe(event_class, method)
