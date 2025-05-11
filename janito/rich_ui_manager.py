from rich.console import Console
from rich.markdown import Markdown
from rich.pretty import Pretty
from janito.event_bus.handler import EventHandlerBase
import janito.event_types as driver_events

class RichUIManager(EventHandlerBase):
    """
    Handles UI rendering for janito events using Rich.

    - Regular (non-raw) output is printed only for ContentPartFound events.
    - For ResponseReceived events, output is printed only if raw mode is enabled (using Pretty formatting).
    - If raw mode is not enabled, ResponseReceived events produce no output.
    """
    def __init__(self, raw_mode=False):
        self.console = Console()
        self.raw_mode = raw_mode
        super().__init__(driver_events)

    def on_ContentPartFound(self, event):
        content = event.content_part
        if content:
            self.console.print(Markdown(content))
        else:
            self.console.print("[No content part to display]")

    def on_ResponseReceived(self, event):
        response = getattr(event, 'response', None)
        if response is not None:
            if self.raw_mode:
                self.console.print(Pretty(response, expand_all=True))
        # No output if not raw_mode or if response is None

