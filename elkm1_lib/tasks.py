"""Definition of an ElkM1 Task"""
from time import time

from .const import Max, TextDescriptions
from .elements import Element, Elements
from .elk import Elk
from .message import tn_encode


class Task(Element):
    """Class representing an Task"""

    def __init__(
        self, index: int, elk: Elk
    ) -> None:  # pylint: disable=useless-super-delegation
        super().__init__(index, elk)
        self.last_change = None

    def activate(self) -> None:
        """(Helper) Activate task"""
        self._elk.send(tn_encode(self._index))


class Tasks(Elements):
    """Handling for multiple tasks"""

    def __init__(self, elk: Elk) -> None:
        super().__init__(elk, Task, Max.TASKS.value)
        elk.add_handler("TC", self._tc_handler)

    def sync(self) -> None:
        """Retrieve tasks from ElkM1"""
        self.get_descriptions(TextDescriptions.TASK.value)

    def _tc_handler(self, task: int) -> None:
        self.elements[task].setattr("last_change", time(), True)
