"""Definition of an ElkM1 Light"""

from .connection import Connection
from .const import Max, TextDescriptions
from .elements import Element, Elements
from .message import pc_encode, pf_encode, pn_encode, ps_encode, pt_encode
from .notify import Notifier


class Light(Element):
    """Class representing a Light"""

    def __init__(self, index: int, connection: Connection, notifier: Notifier) -> None:
        super().__init__(index, connection, notifier)
        self.status = 0

    def level(self, level: int, time: int = 0) -> None:
        """(Helper) Set light to specified level"""
        if level <= 0:
            self._connection.send(pf_encode(self._index))
        elif level >= 98:
            self._connection.send(pn_encode(self._index))
        else:
            self._connection.send(pc_encode(self._index, 9, level, time))

    def toggle(self) -> None:
        """(Helper) Toggle light"""
        self._connection.send(pt_encode(self._index))


class Lights(Elements[Light]):
    """Handling for multiple lights"""

    def __init__(self, connection: Connection, notifier: Notifier) -> None:
        super().__init__(connection, notifier, Light, Max.LIGHTS.value)
        notifier.attach("PC", self._pc_handler)
        notifier.attach("PS", self._ps_handler)

    def sync(self) -> None:
        """Retrieve lights from ElkM1"""
        for i in range(4):
            self._connection.send(ps_encode(i))
        self.get_descriptions(TextDescriptions.LIGHT.value)

    def _pc_handler(self, housecode: str, index: int, light_level: int) -> None:
        self.elements[index].setattr("status", light_level, True)

    def _ps_handler(self, bank: int, statuses: list[int]) -> None:
        for i in range(bank * 64, (bank + 1) * 64):
            self.elements[i].setattr("status", statuses[i - bank * 64], True)
