"""Definition of an ElkM1 Light"""

from .const import Max, TextDescriptions
from .elements import Element, Elements
from .message import pc_encode, pf_encode, pn_encode, ps_encode, pt_encode


class Light(Element):
    """Class representing a Light"""

    def __init__(self, index, elk):
        super().__init__(index, elk)
        self.status = 0

    def level(self, level, time=0):
        """(Helper) Set light to specified level"""
        if level <= 0:
            self._elk.send(pf_encode(self._index))
        elif level >= 98:
            self._elk.send(pn_encode(self._index))
        else:
            self._elk.send(pc_encode(self._index, 9, level, time))

    def toggle(self):
        """(Helper) Toggle light"""
        self._elk.send(pt_encode(self._index))


class Lights(Elements):
    """Handling for multiple lights"""

    def __init__(self, elk):
        super().__init__(elk, Light, Max.LIGHTS.value)
        elk.add_handler("PC", self._pc_handler)
        elk.add_handler("PS", self._ps_handler)

    def sync(self):
        """Retrieve lights from ElkM1"""
        for i in range(4):
            self.elk.send(ps_encode(i))
        self.get_descriptions(TextDescriptions.LIGHT.value)

    def _pc_handler(
        self, housecode, index, light_level
    ):  # pylint: disable=unused-argument
        self.elements[index].setattr("status", light_level, True)

    def _ps_handler(self, bank, statuses):
        for i in range(bank * 64, (bank + 1) * 64):
            self.elements[i].setattr("status", statuses[i - bank * 64], True)
