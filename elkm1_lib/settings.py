"""Definition of an ElkM1 Custom Value"""

from __future__ import annotations

from typing import Any, cast

from .connection import Connection
from .const import Max, TextDescriptions
from .elements import Element, Elements
from .message import cp_encode, cw_encode
from .notify import Notifier


class Setting(Element):
    """Class representing an Custom Value"""

    def __init__(self, index: int, connection: Connection, notifier: Notifier) -> None:
        super().__init__(index, connection, notifier)
        self.value_format = 0
        self.value = None

    def set(self, value: int | tuple[int, int]) -> None:
        """(Helper) Set custom value."""
        self._connection.send(cw_encode(self._index, value, self.value_format))


class Settings(Elements):
    """Handling for multiple custom values"""

    def __init__(self, connection: Connection, notifier: Notifier) -> None:
        super().__init__(connection, notifier, Setting, Max.SETTINGS.value)
        notifier.attach("CR", self._cr_handler)

    def sync(self) -> None:
        """Retrieve custom values from ElkM1"""
        self._connection.send(cp_encode())
        self.get_descriptions(TextDescriptions.SETTING.value)

    def _cr_handler(self, values: list[dict[str, Any]]) -> None:
        settings: list[Setting] = cast(list[Setting], self.elements)
        for value in values:
            setting = settings[value["index"]]
            setting.value_format = value["value_format"]
            setting.value = value["value"]
