"""Definition of an ElkM1 Area"""

import datetime as dt
import time
from typing import Any

from .connection import Connection
from .const import ElkRPStatus
from .elements import Element
from .message import lw_encode, rw_encode, sp_encode, ss_encode, sw_encode, vn_encode
from .notify import Notifier


class Panel(Element):
    """Class representing the overall Elk panel"""

    def __init__(self, connection: Connection, notifier: Notifier) -> None:
        super().__init__(0, connection, notifier)
        self.real_time_clock = None
        self.elkm1_version = None
        self.xep_version = None
        self.remote_programming_status = 0
        self.system_trouble_status = ""
        self.temperature_units = None
        self.user_code_length = None
        self._configured = True
        self.setattr("name", "ElkM1", True)

        notifier.attach("VN", self._vn_handler)
        notifier.attach("XK", self._xk_handler)
        notifier.attach("RR", self._xk_handler)  # RR/XK use same handler
        notifier.attach("RP", self._rp_handler)
        notifier.attach("SS", self._ss_handler)
        notifier.attach("UA", self._ua_handler)

    def sync(self) -> None:
        """Retrieve panel information from ElkM1"""
        self._connection.send(vn_encode())
        self._connection.send(lw_encode())
        self._connection.send(ss_encode())
        # Don't sync UA from here as it is used as a "sync complete" marker

    def speak_word(self, word: int) -> None:
        """(Helper) Speak word."""
        self._connection.send(sw_encode(word))

    def speak_phrase(self, phrase: int) -> None:
        """(Helper) Speak phrase."""
        self._connection.send(sp_encode(phrase))

    def set_time(self, datetime: dt.datetime | None = None) -> None:
        """(Helper) Set the time given a datetime."""
        if datetime is None:
            struct_time = time.localtime()
            datetime = dt.datetime(*struct_time[:6])
        self._connection.send(rw_encode(datetime))

    def _vn_handler(self, elkm1_version: str, xep_version: str) -> None:
        self.setattr("elkm1_version", elkm1_version, False)
        self.setattr("xep_version", xep_version, True)

    def _xk_handler(self, real_time_clock: str) -> None:
        self.setattr("real_time_clock", real_time_clock, True)

    def _ss_handler(self, system_trouble_status: str) -> None:
        def _get_status(index: int, trouble: str, zone_encoded: bool = False) -> None:
            if system_trouble_status[index] != "0":
                if zone_encoded:
                    zone = ord(system_trouble_status[index]) - 0x30
                    statuses.append(f"{trouble} zone {zone}")
                else:
                    statuses.append(trouble)

        statuses: list[str] = []
        _get_status(0, "AC Fail")
        _get_status(1, "Box Tamper", True)
        _get_status(2, "Fail To Communicate")
        _get_status(3, "EEProm Memory Error")
        _get_status(4, "Low Battery Control")
        _get_status(5, "Transmitter Low Battery", True)
        _get_status(6, "Over Current")
        _get_status(7, "Telephone Fault")
        _get_status(9, "Output 2")
        _get_status(10, "Missing Keypad")
        _get_status(11, "Zone Expander")
        _get_status(12, "Output Expander")
        _get_status(14, "ELKRP Remote Access")
        _get_status(16, "Common Area Not Armed")
        _get_status(17, "Flash Memory Error")
        _get_status(18, "Security Alert", True)
        _get_status(19, "Serial Port Expander")
        _get_status(20, "Lost Transmitter", True)
        _get_status(21, "GE Smoke CleanMe")
        _get_status(22, "Ethernet")
        _get_status(31, "Display Message In Keypad Line 1")
        _get_status(32, "Display Message In Keypad Line 2")
        _get_status(33, "Fire", True)
        self.setattr("system_trouble_status", ", ".join(statuses), True)

    def _rp_handler(self, remote_programming_status: ElkRPStatus) -> None:
        if remote_programming_status == ElkRPStatus.DISCONNECTED:
            self._connection.resume()
        else:
            self._connection.pause()
        self.setattr("remote_programming_status", remote_programming_status, True)

    def _ua_handler(self, **kwargs: dict[str, Any]) -> None:
        self.setattr("user_code_length", kwargs["user_code_length"], False)
        self.setattr("temperature_units", kwargs["temperature_units"], True)
