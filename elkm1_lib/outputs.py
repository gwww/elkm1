"""Definition of an ElkM1 Output"""

from .connection import Connection
from .const import Max, TextDescriptions
from .elements import Element, Elements
from .message import cf_encode, cn_encode, cs_encode, ct_encode
from .notify import Notifier


class Output(Element):
    """Class representing an Output"""

    def __init__(self, index: int, connection: Connection, notifier: Notifier) -> None:
        super().__init__(index, connection, notifier)
        self.output_on = False

    def turn_off(self) -> None:
        """(Helper) Turn of an output"""
        self._connection.send(cf_encode(self._index))

    def turn_on(self, time: int) -> None:
        """(Helper) Turn on an output"""
        self._connection.send(cn_encode(self._index, time))

    def toggle(self) -> None:
        """(Helper) Toggle an output"""
        self._connection.send(ct_encode(self._index))


class Outputs(Elements[Output]):
    """Handling for multiple areas"""

    def __init__(self, connection: Connection, notifier: Notifier) -> None:
        super().__init__(connection, notifier, Output, Max.OUTPUTS.value)
        notifier.attach("CC", self._cc_handler)
        notifier.attach("CS", self._cs_handler)

    def sync(self) -> None:
        """Retrieve areas from ElkM1"""
        self._connection.send(cs_encode())
        self.get_descriptions(TextDescriptions.OUTPUT.value)

    def _cc_handler(self, output: int, output_status: bool) -> None:
        self.elements[output].setattr("output_on", output_status, True)

    def _cs_handler(self, output_status: list[bool]) -> None:
        for output in self.elements:
            output.setattr("output_on", output_status[output.index], True)
