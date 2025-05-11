from rich.console import Console
from rich.markdown import Markdown
from rich.pretty import Pretty
from janito.event_bus.handler import EventHandlerBase
import janito.event_types as driver_events

class RichUIManager(EventHandlerBase):
    """
    Listens for ContentPartFound and ResponseReceived events and renders content using Rich.
    """
    def __init__(self):
        self.console = Console()
        super().__init__(driver_events)

    def on_ContentPartFound(self, event):
        content = event.content_part
        if content:
            self.console.print(Markdown(content))
        else:
            self.console.print("[No content part to display]")

    def on_ResponseReceived(self, event):
        # This method now handles what was previously handled by on_RawResponseReceived
        # If you need to distinguish between raw and processed responses, add logic here
        pass

        response = getattr(event, 'response', None)
        if response is not None:
            self.console.print("[bold green]Response:[/bold green]")
            self.console.print(Pretty(response, expand_all=True))
        else:
            self.console.print("[yellow]No response to display.[/yellow]")
