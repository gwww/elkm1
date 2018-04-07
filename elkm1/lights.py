"""Definition of an ElkM1 Light"""

from .const import Max, TextDescriptions
from .elements import Element, Elements
from .message import add_message_handler, ps_encode


class Light(Element):
    """Class representing a Light"""
    def __init__(self, index):
        super().__init__(index)
        self.status = 0

class Lights(Elements):
    """Handling for multiple lights"""
    def __init__(self, elk):
        super().__init__(elk, Light, Max.LIGHTS.value)
        add_message_handler('PC', self._pc_handler)
        add_message_handler('PS', self._ps_handler)

    def sync(self):
        """Retrieve lights from ElkM1"""
        for i in range(4):
            self.elk.send(ps_encode(i))
        self.get_descriptions(TextDescriptions.LIGHT.value)

    # pylint: disable=unused-argument
    def _pc_handler(self, housecode, index, light_level):
        self.elements[index].setattr('status', light_level)

    def _ps_handler(self, bank, statuses):
        for i in range(bank*64, (bank+1)*64):
            self.elements[i].setattr('status', statuses[i-bank*64])
