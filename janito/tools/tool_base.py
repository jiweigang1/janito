from janito.report_events import ReportEvent, ReportSubtype, ReportAction
from janito.event_bus.bus import event_bus as default_event_bus


class ToolBase:
    """
    Base class for all tools in the janito project.
    Extend this class to implement specific tool functionality.
    """
    provides_execution = False  # Indicates if the tool provides execution capability (default: False)

    def __init__(self, name=None, event_bus=None):
        self.name = name or self.__class__.__name__
        self._event_bus = event_bus or default_event_bus

    @property
    def event_bus(self):
        return self._event_bus

    @event_bus.setter
    def event_bus(self, bus):
        self._event_bus = bus or default_event_bus

    def report_action(self, message: str, action: ReportAction, context: dict = None):
        """
        Report that a tool action is starting. This should be the first reporting call for every tool action.
        """
        self._event_bus.publish(
            ReportEvent(
                subtype=ReportSubtype.ACTION_INFO,
                message="  " + message,
                action=action,
                tool=self.name,
                context=context,
            )
        )

    def report_info(self, message: str, context: dict = None):
        self._event_bus.publish(
            ReportEvent(
                subtype=ReportSubtype.ACTION_INFO,
                message=message,
                action=None,
                tool=self.name,
                context=context,
            )
        )

    def report_error(self, message: str, context: dict = None):
        self._event_bus.publish(
            ReportEvent(
                subtype=ReportSubtype.ERROR,
                message=message,
                action=None,
                tool=self.name,
                context=context,
            )
        )

    def report_success(self, message: str, context: dict = None):
        self._event_bus.publish(
            ReportEvent(
                subtype=ReportSubtype.SUCCESS,
                message=message,
                action=None,
                tool=self.name,
                context=context,
            )
        )

    def report_warning(self, message: str, context: dict = None):
        self._event_bus.publish(
            ReportEvent(
                subtype=ReportSubtype.WARNING,
                message=message,
                action=None,
                tool=self.name,
                context=context,
            )
        )

    def report_stdout(self, message: str, context: dict = None):
        self._event_bus.publish(
            ReportEvent(
                subtype=ReportSubtype.STDOUT,
                message=message,
                action=None,
                tool=self.name,
                context=context,
            )
        )

    def report_stderr(self, message: str, context: dict = None):
        self._event_bus.publish(
            ReportEvent(
                subtype=ReportSubtype.STDERR,
                message=message,
                action=None,
                tool=self.name,
                context=context,
            )
        )

    def run(self, *args, **kwargs):
        raise NotImplementedError("Subclasses must implement the run method.")
