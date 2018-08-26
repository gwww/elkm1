"""Definition of an ElkM1 Output"""
from .const import Max, TextDescriptions
from .elements import Element, Elements
from .message import add_message_handler, cs_encode, cf_encode, \
                     cn_encode, ct_encode


class Output(Element):
    """Class representing an Output"""
    def __init__(self, index, elk):
        super().__init__(index, elk)
        self.output_on = False

    def turn_off(self):
        """(Helper) Turn of an output"""
        self._elk.send(cf_encode(self._index))

    def turn_on(self, time):
        """(Helper) Turn on an output"""
        self._elk.send(cn_encode(self._index, time))

    def toggle(self):
        """(Helper) Toggle an output"""
        self._elk.send(ct_encode(self._index))


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
        self.elements[output].setattr('output_on', output_status, True)

    def _cs_handler(self, output_status):
        for output in self.elements:
            output.setattr('output_on', output_status[output.index], True)
