"""Definition of an ElkM1 Keypad."""
import datetime as dt
from typing import Optional, cast

from .connection import Connection
from .const import KeypadKeys, Max, TextDescriptions
from .elements import Element, Elements
from .message import ka_encode


class Keypad(Element):
    """Class representing an Keypad"""

    def __init__(self, index: int, connection: Connection) -> None:
        super().__init__(index, connection)
        self.area = -1
        self.temperature = -40
        self.last_user_time = dt.datetime.now(dt.timezone.utc)
        self.last_user = -1
        self.code = ""
        self.last_keypress: Optional[tuple[str, int]] = None


class Keypads(Elements):
    """Handling for multiple areas"""

    def __init__(self, connection: Connection) -> None:
        super().__init__(connection, Keypad, Max.KEYPADS.value)
        connection.msg_decode.add_handler("IC", self._ic_handler)
        connection.msg_decode.add_handler("KA", self._ka_handler)
        connection.msg_decode.add_handler("KC", self._kc_handler)
        connection.msg_decode.add_handler("LW", self._lw_handler)
        connection.msg_decode.add_handler("ST", self._st_handler)

    def sync(self) -> None:
        """Retrieve areas from ElkM1"""
        self._connection.send(ka_encode())
        self.get_descriptions(TextDescriptions.KEYPAD.value)

    def _ic_handler(self, code: int, user: int, keypad: int) -> None:
        keypad_ = self.elements[keypad]

        # By setting a time this will force the IC change to always be reported
        keypad_.setattr("last_user_time", dt.datetime.now(dt.timezone.utc), False)

        # If user is negative then invalid code entered
        keypad_.setattr("code", code if user < 0 else "****", False)
        keypad_.setattr("last_user", user, True)

    def _ka_handler(self, keypad_areas: list[int]) -> None:
        for keypad in self.elements:
            if keypad_areas[keypad.index] >= 0:
                keypad.setattr("area", keypad_areas[keypad.index], True)

    def _kc_handler(self, keypad: int, key: int) -> None:
        keypads: list[Keypad] = cast(list[Keypad], self.elements)
        keypads[keypad].last_keypress = None  # Force a change notification
        try:
            name = KeypadKeys(key).name
        except ValueError:
            name = ""
        self.elements[keypad].setattr("last_keypress", (name, key), True)

    def _lw_handler(self, keypad_temps: list[int], zone_temps: list[int]) -> None:
        for keypad in self.elements:
            if keypad_temps[keypad.index] > -40:
                keypad.setattr("temperature", keypad_temps[keypad.index], True)

    def _st_handler(self, group: int, device: int, temperature: int) -> None:
        if group == 1:
            self.elements[device].setattr("temperature", temperature, True)
