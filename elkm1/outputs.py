"""Definition of an ElkM1 Output"""
from .const import Max, TextDescriptions
from .elements import Element, Elements
from .message import add_message_handler, cs_encode


class Output(Element):
    """Class representing an Output"""
    def __init__(self, index):
        super().__init__(index)
        self.output_on = False

class Outputs(Elements):
    """Handling for multiple areas"""
    def __init__(self, elk):
        super().__init__(elk, Output, Max.OUTPUTS.value)
        add_message_handler('CC', self._cc_handler)
        add_message_handler('CS', self._cs_handler)

    def sync(self):
        """Retrieve areas from ElkM1"""
        self.elk.send(cs_encode())
        self.get_descriptions(TextDescriptions.OUTPUT.value)

    def _cc_handler(self, output, output_status):
        self.elements[output].setattr('output_on', output_status)

    def _cs_handler(self, output_status):
        for output in self.elements:
            output.setattr('output_on', output_status[output.index])
