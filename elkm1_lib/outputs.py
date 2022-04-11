"""Definition of an ElkM1 Output"""
from .const import Max, TextDescriptions
from .elements import Element, Elements
from .elk import Elk
from .message import cf_encode, cn_encode, cs_encode, ct_encode


class Output(Element):
    """Class representing an Output"""

    def __init__(self, index: int, elk: Elk) -> None:
        super().__init__(index, elk)
        self.output_on = False

    def turn_off(self) -> None:
        """(Helper) Turn of an output"""
        self._elk.send(cf_encode(self._index))

    def turn_on(self, time: int) -> None:
        """(Helper) Turn on an output"""
        self._elk.send(cn_encode(self._index, time))

    def toggle(self) -> None:
        """(Helper) Toggle an output"""
        self._elk.send(ct_encode(self._index))


class Outputs(Elements):
    """Handling for multiple areas"""

    def __init__(self, elk: Elk) -> None:
        super().__init__(elk, Output, Max.OUTPUTS.value)
        elk.add_handler("CC", self._cc_handler)
        elk.add_handler("CS", self._cs_handler)

    def sync(self) -> None:
        """Retrieve areas from ElkM1"""
        self.elk.send(cs_encode())
        self.get_descriptions(TextDescriptions.OUTPUT.value)

    def _cc_handler(self, output: int, output_status: bool) -> None:
        self.elements[output].setattr("output_on", output_status, True)

    def _cs_handler(self, output_status: list[bool]) -> None:
        for output in self.elements:
            output.setattr("output_on", output_status[output.index], True)
