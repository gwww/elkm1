"""Definition of an ElkM1 Custom Value"""
from .const import Max, TextDescriptions
from .elements import Element, Elements
from .message import add_message_handler, cp_encode, cw_encode


class Setting(Element):
    """Class representing an Custom Value"""
    def __init__(self, index, elk):
        super().__init__(index, elk)
        self.value_format = 0
        self.value = None

    def set(self, value):
        """(Helper) Set custom value."""
        self._elk.send(cw_encode(self._index, value, self.value_format))


class Settings(Elements):
    """Handling for multiple custom values"""
    def __init__(self, elk):
        super().__init__(elk, Setting, Max.SETTINGS.value)
        add_message_handler('CR', self._cr_handler)

    def sync(self):
        """Retrieve custom values from ElkM1"""
        self.elk.send(cp_encode())
        self.get_descriptions(TextDescriptions.SETTING.value)

    def _cr_handler(self, index, value, value_format):
        custom_value = self.elements[index]
        custom_value.value_format = value_format
        custom_value.value = value
