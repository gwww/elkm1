"""Definition of an ElkM1 Custom Value"""
from .const import Max, TextDescriptions
from .elements import Element, Elements
from .message import add_message_handler, cx_encode, cv_encode


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

    def _got_desc(self, descriptions):
        super()._got_desc(descriptions)
        # Only poll counters that have a name defined
        for counter in self.elements:
            if not counter.is_default_name():
                self.elk.send(cv_encode(counter.index))

    def _cv_handler(self, counter, value):
        self.elements[counter].setattr('value', value, True)
