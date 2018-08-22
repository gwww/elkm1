"""Definition of an ElkM1 Area"""
from .const import ElkRPStatus
from .elements import Element
from .message import add_message_handler, vn_encode, lw_encode, sw_encode, sp_encode
from .util import add_sync_handler, call_sync_handlers


class Panel(Element):
    """Class representing an Area"""
    def __init__(self, elk):
        super().__init__(0, elk)
        self.real_time_clock = None
        self.elkm1_version = None
        self.xep_version = None
        self.remote_programming_status = 0
        self.setattr('name', 'ElkM1')
        add_sync_handler(self.sync)

    def sync(self):
        """Retrieve panel information from ElkM1"""
        add_message_handler('VN', self._vn_handler)
        add_message_handler('XK', self._xk_handler)
        add_message_handler('RP', self._rp_handler)
        add_message_handler('IE', call_sync_handlers)
        self._elk.send(vn_encode())
        self._elk.send(lw_encode())

    def speak_word(self, word):
        """(Helper) Speak word."""
        self._elk.send(sw_encode(word))

    def speak_phrase(self, phrase):
        """(Helper) Speak phrase."""
        self._elk.send(sp_encode(phrase))

    def _vn_handler(self, elkm1_version, xep_version):
        self.setattr('elkm1_version', elkm1_version)
        self.setattr('xep_version', xep_version)

    def _xk_handler(self, real_time_clock):
        self.setattr('real_time_clock', real_time_clock)

    def _rp_handler(self, remote_programming_status):
        if remote_programming_status == ElkRPStatus.DISCONNECTED.value:
            self._elk.resume()
        else:
            self._elk.pause()
        self.setattr('remote_programming_status', remote_programming_status)
