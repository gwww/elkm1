"""Definition of an ElkM1 Custom Value"""

from __future__ import annotations

from .connection import Connection
from .const import Max, TextDescriptions
from .elements import Element, Elements
from .message import cv_encode, cx_encode
from .notify import Notifier


class Counter(Element):
    """Class representing an Counter"""

    def __init__(self, index: int, connection: Connection, notifier: Notifier) -> None:
        super().__init__(index, connection, notifier)
        self.value = None

    def get(self) -> None:
        """(Helper) Get counter"""
        self._connection.send(cv_encode(self._index))

    def set(self, value: int) -> None:
        """(Helper) Set counter to value"""
        self._connection.send(cx_encode(self._index, value))


class Counters(Elements[Counter]):
    """Handling for multiple counters"""

    def __init__(self, connection: Connection, notifier: Notifier) -> None:
        super().__init__(connection, notifier, Counter, Max.COUNTERS.value)
        notifier.attach("CV", self._cv_handler)

    def sync(self) -> None:
        """Retrieve values from ElkM1 on demand"""
        self.get_descriptions(TextDescriptions.COUNTER.value)

    def _got_desc(self, descriptions: list[str | None], desc_type: int) -> None:
        super()._got_desc(descriptions, desc_type)
        # Only poll counters that have a name defined
        for counter in self.elements:
            if not counter.is_default_name():
                self._connection.send(cv_encode(counter.index), priority_send=True)

    def _cv_handler(self, counter: int, value: int) -> None:
        self.elements[counter].setattr("value", value, True)
