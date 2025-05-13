from rich.console import Console
from rich.markdown import Markdown
from rich.pretty import Pretty
from rich.panel import Panel
from rich.text import Text
from janito.event_bus.handler import EventHandlerBase
import janito.driver_events as driver_events
from janito.report_events import ReportSubtype
from janito.event_bus.bus import event_bus

class RichTerminalReporter(EventHandlerBase):
    """
    Handles UI rendering for janito events using Rich.

    - Regular (non-raw) output is printed only for ContentPartFound events.
    - For RequestFinished events, output is printed only if raw mode is enabled (using Pretty formatting).
    - If raw mode is not enabled, RequestFinished events produce no output.
    - Report events (info, success, error, etc.) are always printed with appropriate styling.
    """
    def __init__(self, raw_mode=False):
        from janito.console import shared_console
        self.console = shared_console
        self.raw_mode = raw_mode
        import janito.report_events as report_events
        super().__init__(driver_events, report_events)

    def on_ContentPartFound(self, event):
        content = event.content_part
        if content:
            self.console.print(Markdown(content))
            self.console.file.flush()
        else:
            self.console.print("[No content part to display]")
            self.console.file.flush()

    def on_RequestFinished(self, event):
        response = getattr(event, 'response', None)
        if response is not None:
            if self.raw_mode:
                self.console.print(Pretty(response, expand_all=True))
                self.console.file.flush()
            # Check for 'code' and 'event' fields in the response
            code = None
            event_field = None
            if isinstance(response, dict):
                code = response.get('code')
                event_field = response.get('event')
            if code is not None:
                self.console.print(f"[bold yellow]Code:[/] {code}")
                self.console.file.flush()
            if event_field is not None:
                self.console.print(f"[bold yellow]Event:[/] {event_field}")
                self.console.file.flush()
        # No output if not raw_mode or if response is None

    def on_ReportEvent(self, event):
        msg = getattr(event, 'message', None)
        subtype = getattr(event, 'subtype', None)
        if not msg or not subtype:
            return
        if subtype == ReportSubtype.ACTION_INFO:
            self.console.print(msg, end="")
            self.console.file.flush()
        elif subtype in (ReportSubtype.SUCCESS, ReportSubtype.ERROR, ReportSubtype.WARNING):
            self.console.print(msg)
            self.console.file.flush()
        else:
            self.console.print(msg)
            self.console.file.flush()
