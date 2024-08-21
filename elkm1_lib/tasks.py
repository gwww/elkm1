"""Definition of an ElkM1 Task"""

from time import time

from .connection import Connection
from .const import Max, TextDescriptions
from .elements import Element, Elements
from .message import tn_encode
from .notify import Notifier


class Task(Element):
    """Class representing an Task"""

    def __init__(self, index: int, connection: Connection, notifier: Notifier) -> None:
        super().__init__(index, connection, notifier)
        self.last_change = None

    def activate(self) -> None:
        """(Helper) Activate task"""
        self._connection.send(tn_encode(self._index))


class Tasks(Elements[Task]):
    """Handling for multiple tasks"""

    def __init__(self, connection: Connection, notifier: Notifier) -> None:
        super().__init__(connection, notifier, Task, Max.TASKS.value)
        notifier.attach("TC", self._tc_handler)

    def sync(self) -> None:
        """Retrieve tasks from ElkM1"""
        self.get_descriptions(TextDescriptions.TASK.value)

    def _tc_handler(self, task: int) -> None:
        self.elements[task].setattr("last_change", time(), True)
