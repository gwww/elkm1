"""Definition of an ElkM1 Custom Value"""

from __future__ import annotations

from typing import Any

from .const import Max, TextDescriptions
from .elements import Element, Elements
from .elk import Elk
from .message import cp_encode, cw_encode


class Setting(Element):
    """Class representing an Custom Value"""

    def __init__(self, index: int, elk: Elk) -> None:
        super().__init__(index, elk)
        self.value_format = 0
        self.value = None

    def set(self, value: int | tuple[int, int]) -> None:
        """(Helper) Set custom value."""
        self._elk.send(cw_encode(self._index, value, self.value_format))


class Settings(Elements):
    """Handling for multiple custom values"""

    def __init__(self, elk: Elk) -> None:
        super().__init__(elk, Setting, Max.SETTINGS.value)
        elk.add_handler("CR", self._cr_handler)

    def sync(self) -> None:
        """Retrieve custom values from ElkM1"""
        self.elk.send(cp_encode())
        self.get_descriptions(TextDescriptions.SETTING.value)

    def _cr_handler(self, values: list[dict[str, Any]]) -> None:
        settings: list[Setting] = getattr(self.elk, "settings")
        for value in values:
            setting = settings[value["index"]]
            setting.value_format = value["value_format"]
            setting.value = value["value"]
