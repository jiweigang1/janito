from dataclasses import dataclass
from typing import ClassVar

@dataclass
class Event:
    """
    Base class for all events in the system.
    Represents a generic event with a category.
    """
    category: ClassVar[str] = "generic"
