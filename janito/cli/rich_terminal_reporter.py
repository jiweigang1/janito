from rich.console import Console
from rich.markdown import Markdown
from rich.pretty import Pretty
from rich.panel import Panel
from rich.text import Text
from janito.event_bus.handler import EventHandlerBase
import janito.driver_events as driver_events
from janito.report_events import ReportSubtype
from janito.event_bus.bus import event_bus
from janito.llm import message_parts

class RichTerminalReporter(EventHandlerBase):
    """
    Handles UI rendering for janito events using Rich.

    - For ResponseReceived events, iterates over the 'parts' field and displays each part appropriately:
        - TextMessagePart: rendered as Markdown (uses 'content' field)
        - Other MessageParts: displayed using Pretty or a suitable Rich representation
    - For RequestFinished events, output is printed only if raw mode is enabled (using Pretty formatting).
    - Report events (info, success, error, etc.) are always printed with appropriate styling.
    """
    def __init__(self, raw_mode=False):
        from janito.cli.console import shared_console
        self.console = shared_console
        self.raw_mode = raw_mode
        import janito.report_events as report_events
        super().__init__(driver_events, report_events)

    def on_ResponseReceived(self, event):
        parts = event.parts if hasattr(event, 'parts') else None
        if not parts:
            self.console.print("[No response parts to display]")
            self.console.file.flush()
            return
        for part in parts:
            if isinstance(part, message_parts.TextMessagePart):
                self.console.print(Markdown(part.content))
                self.console.file.flush()

    def on_RequestFinished(self, event):
        response = event.response if hasattr(event, 'response') else None
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
            if event_field is not None:
                self.console.print(f"[bold yellow]Event:[/] {event_field}")
                self.console.file.flush()
        # No output if not raw_mode or if response is None

    def on_ReportEvent(self, event):
        msg = event.message if hasattr(event, 'message') else None
        subtype = event.subtype if hasattr(event, 'subtype') else None
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
