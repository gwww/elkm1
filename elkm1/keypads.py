"""Definition of an ElkM1 Keypad."""
from .const import Max, TextDescriptions
from .elements import Element, Elements
from .message import add_message_handler, ka_encode


class Keypad(Element):
    """Class representing an Keypad"""
    def __init__(self, index):
        super().__init__(index)
        self.area = None
        self.temperature = None

class Keypads(Elements):
    """Handling for multiple areas"""
    def __init__(self, elk):
        super().__init__(elk, Keypad, Max.KEYPADS.value)
        add_message_handler('KA', self._ka_handler)
        add_message_handler('LW', self._lw_handler)

    def sync(self):
        """Retrieve areas from ElkM1"""
        self.elk.send(ka_encode())
        self.get_descriptions(TextDescriptions.KEYPAD.value)

    def _ka_handler(self, keypad_areas):
        for keypad in self.elements:
            if keypad_areas[keypad.index] >= 0:
                keypad.setattr('area', keypad_areas[keypad.index])

    # pylint: disable=unused-argument
    def _lw_handler(self, keypad_temps, zone_temps):
        for keypad in self.elements:
            if keypad_temps[keypad.index] > -40:
                keypad.setattr('temperature', keypad_temps[keypad.index])
