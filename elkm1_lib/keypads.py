"""Definition of an ElkM1 Keypad."""

import datetime as dt

from .connection import Connection
from .const import FunctionKeys, KeypadKeys, Max, TextDescriptions
from .elements import Element, Elements
from .message import ka_encode, kf_encode
from .notify import Notifier


class Keypad(Element):
    """Class representing an Keypad"""

    def __init__(self, index: int, connection: Connection, notifier: Notifier) -> None:
        super().__init__(index, connection, notifier)
        self.area = -1
        self.temperature = -40
        self.last_user_time = dt.datetime.now(dt.UTC)
        self.last_user = -1
        self.code = ""
        self.last_keypress: tuple[str, int] | None = None
        self.last_function_key = FunctionKeys.FORCE_KF_SYNC

    def press_function_key(self, functionkey: FunctionKeys) -> None:
        """(Helper) Send a function key (1, ... 6, *, C)"""
        self._connection.send(kf_encode(self.index, functionkey))


class Keypads(Elements[Keypad]):
    """Handling for multiple areas"""

    def __init__(self, connection: Connection, notifier: Notifier) -> None:
        super().__init__(connection, notifier, Keypad, Max.KEYPADS.value)
        notifier.attach("IC", self._ic_handler)
        notifier.attach("KA", self._ka_handler)
        notifier.attach("KC", self._kc_handler)
        notifier.attach("KF", self._kf_handler)
        notifier.attach("LW", self._lw_handler)
        notifier.attach("ST", self._st_handler)

    def sync(self) -> None:
        """Retrieve areas from ElkM1"""
        self._connection.send(ka_encode())
        self.get_descriptions(TextDescriptions.KEYPAD.value)
        # Send KF for one of our keypads which reports them all
        self._connection.send(kf_encode(0))

    def _ic_handler(self, code: int, user: int, keypad: int) -> None:
        keypad_ = self.elements[keypad]

        # By setting a time this will force the IC change to always be reported
        keypad_.setattr("last_user_time", dt.datetime.now(dt.UTC), False)

        # If user is negative then invalid code entered
        keypad_.setattr("code", code if user < 0 else "****", False)
        keypad_.setattr("last_user", user, True)

    def _ka_handler(self, keypad_areas: list[int]) -> None:
        for keypad in self.elements:
            if keypad_areas[keypad.index] >= 0:
                keypad.setattr("area", keypad_areas[keypad.index], True)

    def _kc_handler(self, keypad: int, key: int) -> None:
        """
        Handle a keypad change message. At present this function is only handling
        keypresses and does not process function key light changes and beep changes.
        """

        # Ignore NO_KEY as it is not a key press
        if key == KeypadKeys.NO_KEY.value:
            return

        # Force a change notification
        self.elements[keypad].last_keypress = None
        try:
            name = KeypadKeys(key).name
        except ValueError:
            name = ""
        self.elements[keypad].setattr("last_keypress", (name, key), True)

    def _kf_handler(self, keypad: int, key: str, chime_mode: list[int]) -> None:
        # Force a change notification
        self.elements[keypad].last_function_key = FunctionKeys.FORCE_KF_SYNC
        try:
            name = FunctionKeys(key).name
        except ValueError:
            name = ""
        self.elements[keypad].setattr("last_function_key", (name, key), True)

    def _lw_handler(self, keypad_temps: list[int], zone_temps: list[int]) -> None:
        for keypad in self.elements:
            if keypad_temps[keypad.index] > -40:
                keypad.setattr("temperature", keypad_temps[keypad.index], True)

    def _st_handler(self, group: int, device: int, temperature: int) -> None:
        if group == 1:
            self.elements[device].setattr("temperature", temperature, True)
