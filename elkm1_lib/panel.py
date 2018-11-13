"""Definition of an ElkM1 Area"""
from .const import ElkRPStatus
from .elements import Element
from .message import (add_message_handler, vn_encode, lw_encode,
                      sw_encode, sp_encode, ss_encode)
from .util import add_sync_handler, call_sync_handlers


class Panel(Element):
    """Class representing an Area"""
    def __init__(self, elk):
        super().__init__(0, elk)
        self.real_time_clock = None
        self.elkm1_version = None
        self.xep_version = None
        self.remote_programming_status = 0
        self.system_trouble_status = ''
        self.setattr('name', 'ElkM1', True)
        add_sync_handler(self.sync)

    def sync(self):
        """Retrieve panel information from ElkM1"""
        add_message_handler('VN', self._vn_handler)
        add_message_handler('XK', self._xk_handler)
        add_message_handler('RP', self._rp_handler)
        add_message_handler('IE', call_sync_handlers)
        add_message_handler('SS', self._ss_handler)
        self._elk.send(vn_encode())
        self._elk.send(lw_encode())
        self._elk.send(ss_encode())

    def speak_word(self, word):
        """(Helper) Speak word."""
        self._elk.send(sw_encode(word))

    def speak_phrase(self, phrase):
        """(Helper) Speak phrase."""
        self._elk.send(sp_encode(phrase))

    def _vn_handler(self, elkm1_version, xep_version):
        self.setattr('elkm1_version', elkm1_version, False)
        self.setattr('xep_version', xep_version, True)

    def _xk_handler(self, real_time_clock):
        self.setattr('real_time_clock', real_time_clock, True)

    def _ss_handler(self, system_trouble_status):
        def _get_status(index, trouble, zone_encoded=False):
            if system_trouble_status[index] != '0':
                if zone_encoded:
                    zone = ord(system_trouble_status[index]) - 0x30
                    statuses.append('{} zone {}'.format(trouble, zone))
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
        self.setattr('system_trouble_status', ', '.join(statuses), True)

    def _rp_handler(self, remote_programming_status):
        if remote_programming_status == ElkRPStatus.DISCONNECTED.value:
            self._elk.resume()
        else:
            self._elk.pause()
        self.setattr('remote_programming_status', remote_programming_status, True)
