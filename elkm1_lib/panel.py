"""Definition of an ElkM1 Area"""
import datetime as dt
import time

from .const import ElkRPStatus
from .elements import Element
from .message import lw_encode, rw_encode, sp_encode, ss_encode, sw_encode, vn_encode


class Panel(Element):
    """Class representing the overall Elk panel"""

    def __init__(self, elk):
        super().__init__(0, elk)
        self.real_time_clock = None
        self.elkm1_version = None
        self.xep_version = None
        self.remote_programming_status = 0
        self.system_trouble_status = ""
        self.temperature_units = None
        self.user_code_length = None
        self._configured = True
        self.setattr("name", "ElkM1", True)

        self._elk.add_handler("VN", self._vn_handler)
        self._elk.add_handler("XK", self._xk_handler)
        self._elk.add_handler("RR", self._xk_handler)  # RR/XK use same handler
        self._elk.add_handler("RP", self._rp_handler)
        self._elk.add_handler("IE", self._elk.call_sync_handlers)
        self._elk.add_handler("SS", self._ss_handler)
        self._elk.add_handler("UA", self._ua_handler)

    def sync(self):
        """Retrieve panel information from ElkM1"""
        self._elk.send(vn_encode())
        self._elk.send(lw_encode())
        self._elk.send(ss_encode())
        # Don't sync UA from here as it is used as a "sync complete" marker

    def speak_word(self, word):
        """(Helper) Speak word."""
        self._elk.send(sw_encode(word))

    def speak_phrase(self, phrase):
        """(Helper) Speak phrase."""
        self._elk.send(sp_encode(phrase))

    def set_time(self, datetime=None):
        """(Helper) Set the time given a datetime."""
        if datetime is None:
            struct_time = time.localtime()
            datetime = dt.datetime(*struct_time[:6])
        self._elk.send(rw_encode(datetime))

    def _vn_handler(self, elkm1_version, xep_version):
        self.setattr("elkm1_version", elkm1_version, False)
        self.setattr("xep_version", xep_version, True)

    def _xk_handler(self, real_time_clock):
        self.setattr("real_time_clock", real_time_clock, True)

    def _ss_handler(self, system_trouble_status):
        def _get_status(index, trouble, zone_encoded=False):
            if system_trouble_status[index] != "0":
                if zone_encoded:
                    zone = ord(system_trouble_status[index]) - 0x30
                    statuses.append(f"{trouble} zone {zone}")
                else:
                    statuses.append(trouble)

        statuses = []
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

    def _rp_handler(self, remote_programming_status):
        if remote_programming_status == ElkRPStatus.DISCONNECTED.value:
            self._elk.resume()
        else:
            self._elk.pause()
        self.setattr("remote_programming_status", remote_programming_status, True)

    def _ua_handler(self, **kwargs):
        self.setattr("user_code_length", kwargs["user_code_length"], False)
        self.setattr("temperature_units", kwargs["temperature_units"], True)
