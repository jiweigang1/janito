from janito.report_events import ReportEvent, ReportSubtype, ReportAction
from janito.event_bus.bus import event_bus

class ToolBase:
    """
    Base class for all tools in the janito project.
    Extend this class to implement specific tool functionality.
    """
    def __init__(self, name=None):
        self.name = name or self.__class__.__name__

    def report_info(self, message: str, action: ReportAction, context: dict = None):
        """
        Publish an informational ReportEvent to the event bus.
        :param message: The info message to report.
        :param action: The action type (ReportAction) associated with this info event. (Mandatory)
        :param context: Optional dictionary with extra context or metadata.
        """
        event_bus.publish(ReportEvent(
            subtype=ReportSubtype.ACTION_INFO,
            message=message,
            action=action,
            tool=self.name,
            context=context
        ))

    def report_error(self, message: str, action: ReportAction, context: dict = None):
        """
        Publish an error ReportEvent to the event bus.
        :param message: The error message to report.
        :param action: The action type (ReportAction) associated with this error event. (Mandatory)
        :param context: Optional dictionary with extra context or metadata.
        """
        event_bus.publish(ReportEvent(
            subtype=ReportSubtype.ERROR,
            message=message,
            action=action,
            tool=self.name,
            context=context
        ))

    def report_success(self, message: str, action: ReportAction, context: dict = None):
        """
        Publish a success ReportEvent to the event bus.
        :param message: The success message to report.
        :param action: The action type (ReportAction) associated with this success event. (Mandatory)
        :param context: Optional dictionary with extra context or metadata.
        """
        event_bus.publish(ReportEvent(
            subtype=ReportSubtype.SUCCESS,
            message=message,
            action=action,
            tool=self.name,
            context=context
        ))

    def report_warning(self, message: str, action: ReportAction, context: dict = None):
        """
        Publish a warning ReportEvent to the event bus.
        :param message: The warning message to report.
        :param action: The action type (ReportAction) associated with this warning event. (Mandatory)
        :param context: Optional dictionary with extra context or metadata.
        """
        event_bus.publish(ReportEvent(
            subtype=ReportSubtype.WARNING,
            message=message,
            action=action,
            tool=self.name,
            context=context
        ))

    def report_stdout(self, message: str, action: ReportAction, context: dict = None):
        """
        Publish a stdout ReportEvent to the event bus.
        :param message: The stdout message to report.
        :param action: The action type (ReportAction) associated with this stdout event. (Mandatory)
        :param context: Optional dictionary with extra context or metadata.
        """
        event_bus.publish(ReportEvent(
            subtype=ReportSubtype.STDOUT,
            message=message,
            action=action,
            tool=self.name,
            context=context
        ))

    def report_stderr(self, message: str, action: ReportAction, context: dict = None):
        """
        Publish a stderr ReportEvent to the event bus.
        :param message: The stderr message to report.
        :param action: The action type (ReportAction) associated with this stderr event. (Mandatory)
        :param context: Optional dictionary with extra context or metadata.
        """
        event_bus.publish(ReportEvent(
            subtype=ReportSubtype.STDERR,
            message=message,
            action=action,
            tool=self.name,
            context=context
        ))

    def run(self, *args, **kwargs):
        """Override this method in subclasses to implement tool logic."""
        raise NotImplementedError("Subclasses must implement the run method.")
