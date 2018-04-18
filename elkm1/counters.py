"""Definition of an ElkM1 Custom Value"""
from .const import Max, TextDescriptions
from .elements import Element, Elements
from .message import add_message_handler, cx_encode


class Counter(Element):
    """Class representing an Counter"""
    def __init__(self, index, elk):
        super().__init__(index, elk)
        self.value = None

    def set(self, value):
        """(Helper) Set counter to value"""
        self._elk.send(cx_encode(self._index, value))

# pylint: disable=R0903
class Counters(Elements):
    """Handling for multiple counters"""
    def __init__(self, elk):
        super().__init__(elk, Counter, Max.COUNTERS.value)
        add_message_handler('CV', self._cv_handler)

    def sync(self):
        """Retrieve values from ElkM1 on demand"""
        self.get_descriptions(TextDescriptions.COUNTER.value)

    def _cv_handler(self, counter, value):
        countr = self.elements[counter]
        countr.value = value
